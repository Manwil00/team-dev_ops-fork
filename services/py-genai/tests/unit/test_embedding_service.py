import pytest
from unittest.mock import MagicMock, AsyncMock, patch
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
        "src.services.embedding_service.chromadb.PersistentClient"
    ) as mock_chromadb:

        # Mock instances that the service constructor will use
        mock_google_embed_instance = MagicMock()
        mock_google_embed_instance.embed_documents = MagicMock(
            return_value=[[1.0, 1.1], [2.0, 2.1]]
        )
        mock_google_client.return_value = mock_google_embed_instance

        mock_db_instance = MagicMock()
        mock_collection = MagicMock()
        mock_collection.get = MagicMock(
            return_value={"ids": [], "embeddings": [], "documents": []}
        )
        mock_collection.add = MagicMock()
        mock_db_instance.get_or_create_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_db_instance

        # Yield the service instance along with the mocks for assertion
        service = EmbeddingService()
        yield service, mock_collection, mock_google_embed_instance


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
    service, mock_collection, mock_google_embed = mock_embedding_service
    texts = ["new text 1", "new text 2"]
    ids = ["new1", "new2"]

    # Mock DB returning nothing
    mock_collection.get.return_value = {"ids": [], "embeddings": [], "documents": []}

    # Act
    result = await service.embed_batch_with_cache(texts, ids)

    # Assert
    assert result["cached_count"] == 0
    assert len(result["vectors"]) == 2
    mock_collection.get.assert_called_once_with(ids=ids, include=["embeddings"])
    mock_google_embed.embed_documents.assert_called_once_with(texts)
    mock_collection.add.assert_called_once()


@pytest.mark.asyncio
async def test_embed_batch_with_cache_some_cached(mock_embedding_service):
    """
    Tests embed_batch_with_cache when some texts are already in the cache.
    """
    service, mock_collection, mock_google_embed = mock_embedding_service
    texts = ["cached text", "new text"]
    ids = ["cached1", "new1"]

    # Mock DB returning one cached item
    mock_collection.get.return_value = {
        "ids": ["cached1"],
        "embeddings": [[0.5, 0.6]],
        "documents": ["cached text"],
    }
    # Google client will be called with the remaining text
    mock_google_embed.embed_documents.return_value = [[1.0, 1.1]]

    # Act
    result = await service.embed_batch_with_cache(texts, ids)

    # Assert
    assert result["cached_count"] == 1
    assert len(result["vectors"]) == 2
    assert result["vectors"][0] == [0.5, 0.6]  # Cached vector
    assert result["vectors"][1] == [1.0, 1.1]  # New vector
    mock_collection.get.assert_called_once_with(ids=ids, include=["embeddings"])
    mock_google_embed.embed_documents.assert_called_once_with(["new text"])
    mock_collection.add.assert_called_once()
