import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from src.main import app  # Import the FastAPI app instance
from src.routers.classification import openweb_client

client = TestClient(app)


# Mock the attrs response object that openweb_client returns
@pytest.fixture
def mock_openweb_client(mocker):
    # This is the object that openweb_client.classify_source returns
    mock_response = MagicMock()
    mock_response.source = "arxiv"
    mock_response.suggested_category = "Artificial Intelligence"

    # Patch the method on the imported instance
    mocker.patch.object(openweb_client, "classify_source", return_value=mock_response)
    return openweb_client


def test_classify_query_success(mock_openweb_client):
    """
    Tests the happy path for the /classify endpoint.
    Verifies that a valid request returns a 200 OK and the expected response body.
    """
    # Arrange
    request_body = {"query": "What are the latest trends in AI?"}

    # Act
    response = client.post("/api/v1/classify", json=request_body)

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["source"] == "arxiv"
    assert json_response["source_type"] == "research"
    assert json_response["suggested_category"] == "Artificial Intelligence"
    mock_openweb_client.classify_source.assert_called_once_with(
        "What are the latest trends in AI?"
    )


def test_classify_query_empty_query():
    """
    Tests the error path for the /classify endpoint when the query is empty.
    Verifies that the endpoint returns a 400 Bad Request.
    """
    # Arrange
    request_body = {"query": " "}  # Empty or whitespace-only query

    # Act
    response = client.post("/api/v1/classify", json=request_body)

    # Assert
    assert response.status_code == 400
    json_response = response.json()
    assert json_response["detail"]["code"] == "INVALID_REQUEST"
    assert "Query cannot be empty" in json_response["detail"]["message"]


def test_classify_query_no_query():
    """
    Tests the error path for the /classify endpoint when the query field is missing.
    FastAPI should handle this and return a 422 Unprocessable Entity.
    """
    # Arrange
    request_body = {}  # Missing 'query' field

    # Act
    response = client.post("/api/v1/classify", json=request_body)

    # Assert
    assert response.status_code == 422
