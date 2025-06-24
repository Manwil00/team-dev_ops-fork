from fastapi import APIRouter, HTTPException
import logging
from ..models.schemas import TrendsRequest, TrendsResponse
from ..services.topic_discovery_service import topic_discovery_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["trends"])

@router.post("/topic-discovery", response_model=TrendsResponse)
async def topic_discovery(req: TrendsRequest):
    """Extract trending topics using semantic clustering"""
    try:
        logger.info(f"Extracting topics for feed_url: {req.feed_url}")
        
        result = topic_discovery_service.extract_topics(
            feed_url=req.feed_url,
            max_articles=req.max_articles,
            min_frequency=req.min_frequency
        )
        
        return TrendsResponse(
            query=req.query,
            feed_url=req.feed_url,
            trends=result["topics"],
            total_articles_processed=result["articles_processed"]
        )
    
    except Exception as e:
        logger.error(f"Error extracting topics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 