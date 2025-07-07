import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock

from src.main import app
from niche_explorer_models.models.topic_discovery_response import TopicDiscoveryResponse


# This fixture will patch the TopicDiscoveryService where it's instantiated in main.py
@pytest.fixture
def mock_topic_service():
    with patch("src.main.topic_service", new_callable=MagicMock) as mock_service:
        # We need to mock the async method on the instance
        mock_service.discover_topic = AsyncMock()
        yield mock_service


client = TestClient(app)


def test_discover_topics_success(mock_topic_service):
    """
    Tests the happy path for POST /api/v1/topics/discover.
    """
    # Arrange
    request_body = {
        "query": "Test Query",
        "article_ids": ["1", "2"],
        "articles": [
            {"id": "1", "title": "Art 1", "source": "arxiv", "link": "http://a.com"},
            {"id": "2", "title": "Art 2", "source": "arxiv", "link": "http://b.com"},
        ],
    }
    # Configure the mock to return a valid response model
    mock_topic_service.discover_topic.return_value = TopicDiscoveryResponse(
        query="Test Query", topics=[], total_articles_processed=2
    )

    # Act
    response = client.post("/api/v1/topics/discover", json=request_body)

    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["query"] == "Test Query"
    assert json_data["total_articles_processed"] == 2
    mock_topic_service.discover_topic.assert_awaited_once()


def test_discover_topics_service_failure(mock_topic_service):
    """
    Tests that a 500 error is returned if the topic discovery service fails.
    """
    # Arrange
    # Send a valid request to bypass the initial validation
    request_body = {
        "query": "Test Query",
        "article_ids": ["1"],
        "articles": [
            {"id": "1", "title": "Art 1", "source": "arxiv", "link": "http://a.com"}
        ],
    }
    mock_topic_service.discover_topic.side_effect = Exception("Clustering failed")

    # Act
    response = client.post("/api/v1/topics/discover", json=request_body)

    # Assert
    assert response.status_code == 500
    assert "Failed to discover topics" in response.json()["detail"]


# Need to import AsyncMock for this to work correctly in the fixture
