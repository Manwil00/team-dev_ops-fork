import logging
from typing import List, Dict
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import arxiv
from ..config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.embeddings_client = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.db_client = chromadb.PersistentClient(path="/app/chroma_db")
        self.collection = self.db_client.get_or_create_collection(name="arxiv_embeddings")

    def embed_text(self, text: str) -> List[float]:
        """Generates a single, non-cached embedding for a given text."""
        try:
            return self.embeddings_client.embed_query(text)
        except Exception as e:
            logger.error("Embedding failed for text: %s, error: %s", text[:100], e)
            return []

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """A private method to generate embeddings for multiple texts."""
        try:
            return self.embeddings_client.embed_documents(texts)
        except Exception as e:
            logger.error("Batch embedding failed: %s", e)
            return [[] for _ in texts]

    def get_embeddings(self, articles: List[arxiv.Result]) -> Dict[str, List[float]]:
        """
        Retrieves embeddings for a list of articles. First, it tries to fetch the
        embeddings from the cache (ChromaDB). For any articles not found in the
        cache, it generates new embeddings and stores them.
        """
        article_ids = [a.get_short_id() for a in articles]
        embeddings_map = {}

        # 1. Try to get existing embeddings from the database
        try:
            cached_results = self.collection.get(ids=article_ids, include=["embeddings"])
            cached_ids = set(cached_results['ids'])
            embeddings_map.update({id: emb for id, emb in zip(cached_results['ids'], cached_results['embeddings'])})
            if cached_ids:
                logger.info(f"Read {len(cached_ids)} embeddings from cache.")
        except Exception as e:
            logger.error(f"Error fetching from ChromaDB: {e}")
            cached_ids = set()

        # 2. Identify articles that need new embeddings
        new_articles = [article for article in articles if article.get_short_id() not in cached_ids]
        
        # 3. Generate and store embeddings for new articles
        if new_articles:
            logger.info(f"Generating and storing embeddings for {len(new_articles)} new articles.")
            
            texts_to_embed = [f"{article.title} - {article.summary}" for article in new_articles]
            new_embeddings = self._embed_batch(texts_to_embed)
            
            new_article_ids = [article.get_short_id() for article in new_articles]
            
            # Add new embeddings to ChromaDB
            if new_article_ids:
                try:
                    self.collection.add(
                        embeddings=new_embeddings,
                        documents=[f"{a.title} - {a.summary}" for a in new_articles],
                        metadatas=[{"title": a.title, "link": str(a.links[0])} for a in new_articles],
                        ids=new_article_ids
                    )
                    logger.info(f"Successfully stored {len(new_article_ids)} new embeddings.")
                    # Add the newly created embeddings to our map
                    embeddings_map.update({id: emb for id, emb in zip(new_article_ids, new_embeddings)})
                except Exception as e:
                    logger.error(f"Error storing new embeddings in ChromaDB: {e}")
            
        return embeddings_map

# Singleton instance
embedding_service = EmbeddingService() 