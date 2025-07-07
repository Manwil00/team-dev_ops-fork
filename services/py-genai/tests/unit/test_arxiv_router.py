import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.main import app


# Mock the service instance used by the router
@pytest.fixture
def mock_query_service(mocker):
    mock = MagicMock()
    mocker.patch("src.routers.arxiv.query_service", new=mock)
    return mock


client = TestClient(app)


def test_build_arxiv_query_success(mock_query_service):
    """
    Tests the happy path for building an arXiv query.
    """
    # Arrange
    mock_query_service.build_advanced_query.return_value = (
        'all:"test terms"+AND+cat:cs.TEST'
    )
    request_body = {"search_terms": "test terms", "filters": {"category": "cs.TEST"}}

    # Act
    response = client.post("/api/v1/query/build/arxiv", json=request_body)

    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["source"] == "arxiv"
    assert json_data["query"] == 'all:"test terms"+AND+cat:cs.TEST'
    mock_query_service.build_advanced_query.assert_called_once_with(
        "test terms", "cs.TEST"
    )


def test_build_query_unsupported_source(mock_query_service):
    """
    Tests that an unsupported source returns a 400 error.
    """
    # Arrange
    request_body = {"search_terms": "test"}

    # Act
    response = client.post("/api/v1/query/build/unsupported", json=request_body)

    # Assert
    assert response.status_code == 400
    assert "Unsupported source" in response.json()["detail"]


def test_build_arxiv_query_no_category(mock_query_service):
    """
    Tests that a default category is used for arXiv if none is provided.
    """
    # Arrange
    mock_query_service.build_advanced_query.return_value = (
        'all:"test terms"+AND+cat:cs.CV'
    )
    request_body = {"search_terms": "test terms"}  # No filters.category

    # Act
    response = client.post("/api/v1/query/build/arxiv", json=request_body)

    # Assert
    assert response.status_code == 200
    mock_query_service.build_advanced_query.assert_called_once_with(
        "test terms", "cs.CV"
    )


def test_build_query_service_exception(mock_query_service):
    """
    Tests that a 500 error is returned if the underlying service fails.
    """
    # Arrange
    mock_query_service.build_advanced_query.side_effect = Exception("Service Error")
    request_body = {"search_terms": "test"}

    # Act
    response = client.post("/api/v1/query/build/arxiv", json=request_body)

    # Assert
    assert response.status_code == 500
    assert "Failed to build query: Service Error" in response.json()["detail"]
