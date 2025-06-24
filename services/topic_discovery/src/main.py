from fastapi import FastAPI, HTTPException
from .services.topic_service import topic_service
from .models import TrendsRequest, TrendsRequestWithKeys, TrendsResponse
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Topic Discovery Service (Lightweight)", version="0.1.0")

@app.post("/topic-discovery", response_model=TrendsResponse)
async def topic_discovery(req: TrendsRequest):
    """Original endpoint - fetches articles from arXiv and generates embeddings"""
    try:
        logger.info("Discovering topics for query=%s", req.query)
        result = await topic_service.discover_topics(
            query=req.query,
            max_results=req.max_articles,
            min_cluster_size=req.min_frequency or 3  # Map min_frequency to min_cluster_size
        )
        
        return TrendsResponse(
            query=req.query,
            feed_url=req.feed_url,
            trends=result["topics"],  # Map "topics" to "trends"
            total_articles_processed=result["total_articles"]  # Map field name
        )
    except Exception as e:
        logger.error("Error in topic discovery: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/topic-discovery-with-keys", response_model=TrendsResponse)
async def topic_discovery_with_keys(req: TrendsRequestWithKeys):
    """API-first endpoint - uses pre-fetched article keys and loads from ChromaDB"""
    try:
        logger.info("Discovering topics for query=%s with %d pre-fetched articles", 
                   req.query, len(req.article_keys))
        result = await topic_service.discover_topics_with_keys(
            query=req.query,
            article_keys=req.article_keys,
            articles=req.articles,
            min_cluster_size=req.min_cluster_size
        )
        
        return TrendsResponse(
            query=req.query,
            feed_url=None,
            trends=result["topics"],  # Map "topics" to "trends"
            total_articles_processed=result["total_articles"]  # Map field name
        )
    except Exception as e:
        logger.error("Error in topic discovery with keys: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/discover-topics-from-embeddings", response_model=TrendsResponse)
async def discover_topics_from_embeddings(req: TrendsRequestWithKeys):
    """
    Proper REST architecture endpoint:
    Uses cached embeddings from GenAI service (assumes embeddings already stored in ChromaDB)
    """
    try:
        logger.info("Discovering topics from cached embeddings for query=%s with %d articles", 
                   req.query, len(req.article_keys))
        result = await topic_service.discover_topics_from_cached_embeddings(
            query=req.query,
            article_keys=req.article_keys,
            articles=req.articles,
            min_cluster_size=req.min_cluster_size
        )
        
        return TrendsResponse(
            query=req.query,
            feed_url=None,
            trends=result["topics"],  # Map "topics" to "trends"
            total_articles_processed=result["total_articles"]  # Map field name
        )
    except Exception as e:
        logger.error("Error in topic discovery from embeddings: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "ok", "service": "topic-discovery"} 