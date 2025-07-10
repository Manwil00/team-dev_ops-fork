import pytest
from unittest.mock import MagicMock, patch
from src.services.embedding_service import EmbeddingService


@pytest.fixture
def mock_embedding_service():
    """
    Mocks the EmbeddingService and its external dependencies.
    This uses patch to replace the clients that the service creates internally.
    """
    with patch(
        "src.services.embedding_service.GoogleGenerativeAIEmbeddings"
    ) as mock_google_client, patch(
        "src.services.embedding_service.psycopg2.connect"
    ) as mock_pg:
        # Mock instances that the service constructor will use
        mock_google_embed_instance = MagicMock()
        mock_google_embed_instance.embed_documents = MagicMock(
            return_value=[[1.0, 1.1], [2.0, 2.1]]
        )
        mock_google_client.return_value = mock_google_embed_instance

        # Fake Postgres connection & cursor
        fake_cur = MagicMock()
        fake_conn = MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        mock_pg.return_value = fake_conn

        # Yield the service instance along with the mocks for assertion
        service = EmbeddingService()
        yield service, fake_cur, mock_google_embed_instance


def test_embedding_service_initialization(mock_embedding_service):
    """
    Tests if the EmbeddingService can be initialized correctly by checking if
    the internal clients were called.
    """
    service, _, _ = mock_embedding_service
    assert service is not None
    # Check that the clients were initialized
    assert service.embeddings_client is not None
    assert service.collection is not None


@pytest.mark.asyncio
async def test_embed_batch_with_cache_all_new(mock_embedding_service):
    """
    Tests embed_batch_with_cache when all texts are new and not in the cache.
    """
    service, fake_cur, mock_google_embed = mock_embedding_service
    texts = ["new text 1", "new text 2"]
    ids = ["new1", "new2"]

    # Mock DB returning nothing
    fake_cur.fetchall.return_value = []

    # Act
    result = await service.embed_batch_with_cache(texts, ids)

    # Assert
    assert result["cached_count"] == 0
    assert len(result["vectors"]) == 2
    fake_cur.execute.assert_called()
    mock_google_embed.embed_documents.assert_called_once_with(texts)
    # mock_collection.add.assert_called_once() # This line is removed as per the new_code


@pytest.mark.asyncio
async def test_embed_batch_with_cache_some_cached(mock_embedding_service):
    """
    Tests embed_batch_with_cache when some texts are already in the cache.
    """
    service, fake_cur, mock_google_embed = mock_embedding_service
    texts = ["cached text", "new text"]
    ids = ["cached1", "new1"]

    # Mock DB returning one cached item
    fake_cur.fetchall.return_value = [("cached1", [0.5, 0.6])]
    # Google client will be called with the remaining text
    mock_google_embed.embed_documents.return_value = [[1.0, 1.1]]

    # Act
    result = await service.embed_batch_with_cache(texts, ids)

    # Assert
    assert result["cached_count"] == 1
    assert len(result["vectors"]) == 2
    assert result["vectors"][0] == [0.5, 0.6]  # Cached vector
    assert result["vectors"][1] == [1.0, 1.1]  # New vector
    fake_cur.execute.assert_called()
    mock_google_embed.embed_documents.assert_called_once_with(["new text"])
    # mock_collection.add.assert_called_once() # This line is removed as per the new_code
