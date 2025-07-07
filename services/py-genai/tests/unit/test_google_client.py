import pytest
from unittest.mock import patch, MagicMock
import json
from src.services.google_client import GoogleGenAIClient


@pytest.fixture
def google_client():
    """Provides a GoogleGenAIClient instance for testing."""
    return GoogleGenAIClient()


@patch("src.services.google_client.genai.GenerativeModel")
def test_classify_source_success(MockGenerativeModel, google_client):
    """
    Tests successful classification when the Google GenAI API returns valid JSON.
    """
    # Arrange
    mock_model_instance = MockGenerativeModel.return_value
    mock_response = MagicMock()
    mock_response_data = {"source": "research", "feed": "cs.AI"}
    mock_response.text = json.dumps(mock_response_data)
    mock_model_instance.generate_content.return_value = mock_response

    # Act
    source, feed = google_client.classify_source("some research query")

    # Assert
    assert source == "research"
    assert feed == "cs.AI"
    mock_model_instance.generate_content.assert_called_once()


@patch("src.services.google_client.genai.GenerativeModel")
def test_classify_source_api_failure(MockGenerativeModel, google_client):
    """
    Tests the fallback mechanism when the Google GenAI API call fails.
    """
    # Arrange
    mock_model_instance = MockGenerativeModel.return_value
    mock_model_instance.generate_content.side_effect = Exception("API is down")

    # Act
    source, feed = google_client.classify_source("a query that will fail")

    # Assert
    assert source == "research"
    assert feed == "cs.CV"


@patch("src.services.google_client.genai.GenerativeModel")
def test_classify_source_invalid_json(MockGenerativeModel, google_client):
    """
    Tests the fallback mechanism when the API returns invalid JSON.
    """
    # Arrange
    mock_model_instance = MockGenerativeModel.return_value
    mock_response = MagicMock()
    mock_response.text = "this is not valid json"
    mock_model_instance.generate_content.return_value = mock_response

    # Act
    source, feed = google_client.classify_source("another query")

    # Assert
    assert source == "research"
    assert feed == "cs.CV"
