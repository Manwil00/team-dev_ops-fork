import logging
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ..config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.embeddings_client = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for given text"""
        try:
            # LangChain embed_query returns a list of floats directly
            embedding = self.embeddings_client.embed_query(text)
            return embedding
        except Exception as e:
            logger.error("Embedding failed for text: %s, error: %s", text[:100], e)
            return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = self.embeddings_client.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error("Batch embedding failed: %s", e)
            return [[] for _ in texts]

# Singleton instance
embedding_service = EmbeddingService() 