import pytest
import json
from unittest.mock import MagicMock, patch
from src.services.openweb_client import OpenWebClient
from niche_explorer_models.models.classify_response import ClassifyResponse


@pytest.fixture
def web_client():
    """Fixture to provide an OpenWebClient instance with a mocked chain."""
    with patch.dict("os.environ", {"CHAIR_API_KEY": "test-key"}):
        client = OpenWebClient()
        # Mock the entire chain object's invoke method
        client.chain = MagicMock()
        return client


def test_classify_source_success(web_client):
    """
    Tests successful classification when the LLM returns valid JSON.
    """
    # Arrange
    query = "some query"
    mock_llm_output = json.dumps(
        {"source": "arxiv", "feed": "cs.AI", "confidence": 0.9}
    )
    web_client.chain.invoke.return_value = mock_llm_output

    # Act
    result = web_client.classify_source(query)

    # Assert
    assert isinstance(result, ClassifyResponse)
    assert result.source == "arxiv"
    assert result.source_type == "research"
    assert result.suggested_category == "cs.AI"
    assert result.confidence == 0.9
    web_client.chain.invoke.assert_called_once_with({"query": query})


def test_classify_source_with_markdown_fences(web_client):
    """
    Tests that the client correctly handles JSON wrapped in markdown fences.
    """
    # Arrange
    query = "another query"
    mock_llm_output = (
        "```json\n"
        + json.dumps({"source": "reddit", "feed": "MachineLearning"})
        + "\n```"
    )
    web_client.chain.invoke.return_value = mock_llm_output

    # Act
    result = web_client.classify_source(query)

    # Assert
    assert result.source == "reddit"
    assert result.source_type == "community"
    assert result.suggested_category == "MachineLearning"


def test_classify_source_invalid_json_fallback(web_client):
    """
    Tests that the client falls back to default values when the LLM returns invalid JSON.
    """
    # Arrange
    query = "a third query"
    web_client.chain.invoke.return_value = "this is not json"

    # Act
    result = web_client.classify_source(query)

    # Assert
    assert result.source == "arxiv"
    assert result.source_type == "research"
    assert result.suggested_category == "cs.CV"
    assert result.confidence == 0.5


def test_classify_source_llm_exception_fallback(web_client):
    """
    Tests that the client falls back to default values when the chain invoke fails.
    """
    # Arrange
    query = "a failing query"
    web_client.chain.invoke.side_effect = Exception("LLM is down")

    # Act
    result = web_client.classify_source(query)

    # Assert
    assert result.source == "arxiv"
    assert result.source_type == "research"
    assert result.suggested_category == "cs.CV"
    assert result.confidence == 0.5
