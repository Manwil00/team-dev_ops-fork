from fastapi import FastAPI, HTTPException
from .services.topic_service import topic_service
from .models import TrendsRequestWithKeys, TrendsResponse
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Topic Discovery Service (Lightweight)", version="0.1.0")

@app.post("/discover-topic", response_model=TrendsResponse)
async def discover_topic(req: TrendsRequestWithKeys):
    """Cluster cached embeddings into coherent research/community topics."""
    try:
        logger.info(
            "Discovering topics for query=%s using %d article embeddings",
            req.query,
            len(req.article_keys),
        )

        result = await topic_service.discover_topic(
            query=req.query,
            article_keys=req.article_keys,
            articles=req.articles,
            min_cluster_size=req.min_cluster_size,
        )

        return TrendsResponse(
            query=req.query,
            feed_url=None,
            trends=result["topics"],
            total_articles_processed=result["total_articles"],
        )
    except Exception as e:
        logger.error("Error in /discover-topic: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "ok", "service": "topic-discovery"} 