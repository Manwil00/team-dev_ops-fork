import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture
def mock_embedding_service():
    """
    Mocks the embedding_service instance within the router module.
    This is the most reliable way to mock for this application's structure.
    It uses AsyncMock for the service's async methods.
    """
    service_instance_mock = MagicMock()
    service_instance_mock.embed_batch_with_cache = AsyncMock()
    service_instance_mock.get_embeddings_by_ids = AsyncMock()

    with patch(
        "src.routers.embedding.embedding_service", service_instance_mock
    ) as mock:
        yield mock


# --- POST /embeddings Tests ---


def test_post_embeddings_all_cache_miss(mock_embedding_service):
    """
    Tests POST /embeddings when no items are in the cache.
    """
    # Arrange
    request_body = {"texts": ["text1", "text2"], "ids": ["id1", "id2"]}
    mock_embedding_service.embed_batch_with_cache.return_value = {
        "vectors": [[1.0, 1.1], [2.0, 2.1]],
        "cached_count": 0,
    }

    # Act
    response = client.post("/api/v1/embeddings", json=request_body)

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["cached_count"] == 0
    assert json_response["embeddings"] == [[1.0, 1.1], [2.0, 2.1]]
    mock_embedding_service.embed_batch_with_cache.assert_awaited_once_with(
        ["text1", "text2"], ["id1", "id2"]
    )


def test_post_embeddings_all_cache_hit(mock_embedding_service):
    """
    Tests POST /embeddings when all items are in the cache.
    """
    # Arrange
    request_body = {"texts": ["text1", "text2"], "ids": ["id1", "id2"]}
    mock_embedding_service.embed_batch_with_cache.return_value = {
        "vectors": [[1.0, 1.1], [2.0, 2.1]],
        "cached_count": 2,
    }

    # Act
    response = client.post("/api/v1/embeddings", json=request_body)

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["cached_count"] == 2
    assert json_response["embeddings"] == [[1.0, 1.1], [2.0, 2.1]]


def test_post_embeddings_service_fails(mock_embedding_service):
    """Tests that a 500 is returned if the service fails on POST."""
    # Arrange
    mock_embedding_service.embed_batch_with_cache.side_effect = Exception(
        "Google is down"
    )
    request_body = {"texts": ["text1"], "ids": ["id1"]}

    # Act
    response = client.post("/api/v1/embeddings", json=request_body)

    # Assert
    assert response.status_code == 500
    assert "Failed to generate embeddings" in response.text


# --- GET /embeddings Tests ---


def test_get_embeddings_success(mock_embedding_service):
    """
    Tests GET /embeddings happy path.
    """
    # Arrange
    mock_embedding_service.get_embeddings_by_ids.return_value = {
        "embeddings": [[1.0, 1.1], [2.0, 2.1]],
        "found_count": 2,
    }

    # Act
    response = client.get("/api/v1/embeddings?ids=id1&ids=id2")

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["found_count"] == 2
    assert json_response["embeddings"] == [[1.0, 1.1], [2.0, 2.1]]
    mock_embedding_service.get_embeddings_by_ids.assert_awaited_once_with(
        ["id1", "id2"]
    )


def test_get_embeddings_partial_found(mock_embedding_service):
    """
    Tests GET /embeddings when only some documents are found.
    """
    # Arrange
    mock_embedding_service.get_embeddings_by_ids.return_value = {
        "embeddings": [[1.0, 1.1], []],
        "found_count": 1,
    }

    # Act
    response = client.get("/api/v1/embeddings?ids=id1&ids=missing")

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["found_count"] == 1
    assert json_response["embeddings"] == [[1.0, 1.1], []]
    mock_embedding_service.get_embeddings_by_ids.assert_awaited_once_with(
        ["id1", "missing"]
    )


def test_get_embeddings_service_fails(mock_embedding_service):
    """Tests that a 500 is returned if the service fails on GET."""
    # Arrange
    mock_embedding_service.get_embeddings_by_ids.side_effect = Exception(
        "Service is down"
    )

    # Act
    response = client.get("/api/v1/embeddings?ids=id1")

    # Assert
    assert response.status_code == 500
    assert "Failed to retrieve embeddings" in response.text
