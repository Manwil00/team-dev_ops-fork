import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import datetime
from src.services.arxiv_service import ArxivFetcher
import arxiv
import requests
from freezegun import freeze_time


@pytest.fixture
def fetcher():
    """Provides a clean ArxivFetcher instance for each test."""
    return ArxivFetcher()


@pytest.fixture
def mock_arxiv_result():
    """Creates a mock arxiv.Result object."""
    result = MagicMock(spec=arxiv.Result)
    result.get_short_id.return_value = "2301.12345"
    result.entry_id = "http://arxiv.org/abs/2301.12345v1"
    result.title = "Test Paper Title"
    result.summary = "This is a summary of the test paper."
    author_mock = MagicMock()
    author_mock.name = "John Doe"
    result.authors = [author_mock]
    result.published = datetime.datetime(
        2023, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc
    )
    return result


@pytest.mark.asyncio
async def test_fetch_success_primary_api(fetcher, mock_arxiv_result):
    """
    Tests successful fetching using the primary arxiv library.
    """
    # Arrange
    with patch.object(
        fetcher.client, "results", return_value=[mock_arxiv_result]
    ) as mock_results:
        # Act
        articles = await fetcher.fetch("cat:cs.AI", max_results=1)

        # Assert
        mock_results.assert_called_once()
        assert len(articles) == 1
        article = articles[0]
        assert article.id == "2301.12345"
        assert article.title == "Test Paper Title"
        assert article.authors == ["John Doe"]
        assert article.source == "arxiv"


@pytest.mark.asyncio
async def test_fetch_fallback_on_empty_primary_result(fetcher, mocker):
    """
    Tests if the service falls back to the HTTP API when the primary method returns no results.
    """
    # Arrange
    mocker.patch.object(fetcher.client, "results", return_value=[])
    mock_http_fallback = mocker.patch(
        "src.services.arxiv_service.ArxivFetcher._fetch_via_http_api",
        new_callable=AsyncMock,
        return_value=[],
    )

    # Act
    await fetcher.fetch("cat:cs.CV", max_results=10)

    # Assert
    mock_http_fallback.assert_awaited_once_with("cat:cs.CV", 10)


@pytest.mark.asyncio
async def test_fetch_fallback_on_arxiv_error(fetcher, mocker):
    """
    Tests if the service falls back to the HTTP API on an ArxivError.
    """
    # Arrange
    mocker.patch.object(
        fetcher.client,
        "results",
        side_effect=arxiv.ArxivError(
            message="test error", retry=0, url="http://example.com"
        ),
    )
    mock_http_fallback = mocker.patch(
        "src.services.arxiv_service.ArxivFetcher._fetch_via_http_api",
        new_callable=AsyncMock,
        return_value=[],
    )

    # Act
    await fetcher.fetch("cat:cs.LG", max_results=5)

    # Assert
    mock_http_fallback.assert_awaited_once_with("cat:cs.LG", 5)


@pytest.mark.asyncio
@freeze_time("2023-10-27")
async def test_http_fallback_parsing(fetcher, mocker):
    """
    Tests the parsing logic of the raw XML feed from the HTTP fallback.
    """
    # Arrange
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2310.12345v1</id>
        <title>HTTP Fallback Paper</title>
        <summary>A summary from the fallback.</summary>
        <author><name>Jane Smith</name></author>
        <published>2023-10-27T10:00:00Z</published>
      </entry>
    </feed>"""
    mocker.patch("requests.get", return_value=mock_response)

    # Act
    articles = await fetcher._fetch_via_http_api("all:test", 1)

    # Assert
    assert len(articles) == 1
    article = articles[0]
    assert article.id == "2310.12345v1"
    assert article.title == "HTTP Fallback Paper"
    assert article.summary == "A summary from the fallback."
    assert article.authors == ["Jane Smith"]
    assert article.published == datetime.datetime(
        2023, 10, 27, 10, 0, 0, tzinfo=datetime.timezone.utc
    )
    assert article.source == "arxiv"
