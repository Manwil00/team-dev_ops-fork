import pytest
from fastapi.testclient import TestClient
import os

# This app import will now happen after the GENAI_BASE_URL is set by the conftest fixture
from src.main import app

client = TestClient(app)


@pytest.mark.integration
def test_discover_topics_with_real_genai_service():
    """
    Tests the POST /api/v1/topics/discover endpoint against a real, containerized
    py-genai service. This test is slow as it involves Docker and real API calls
    made by the py-genai service.
    """
    # This key is passed to the py-genai container during the build
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not found, skipping topics integration test.")

    request_body = {
        "query": "Artificial Intelligence",
        "article_ids": ["id_1", "id_2", "id_3"],
        "articles": [
            {
                "id": "id_1",
                "title": "The Future of AI",
                "summary": "Exploring the trajectory of artificial intelligence.",
                "source": "arxiv",
                "link": "http://example.com/1",
            },
            {
                "id": "id_2",
                "title": "AI in Healthcare",
                "summary": "How AI is revolutionizing the medical field.",
                "source": "arxiv",
                "link": "http://example.com/2",
            },
            {
                "id": "id_3",
                "title": "Machine Learning Models",
                "summary": "A deep dive into popular ML models and algorithms.",
                "source": "arxiv",
                "link": "http://example.com/3",
            },
        ],
    }

    # Act
    response = client.post("/api/v1/topics/discover", json=request_body)

    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["query"] == "Artificial Intelligence"
    assert json_data["total_articles_processed"] == 3
    # We expect at least one topic to be discovered from this data
    assert len(json_data["topics"]) > 0
    # Check the structure of the first topic
    topic = json_data["topics"][0]
    assert "title" in topic
    assert "description" in topic
    assert "article_count" in topic
    assert topic["article_count"] > 0
