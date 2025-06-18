from fastapi import APIRouter, HTTPException
from typing import Optional
from ..models.schemas import TrendsRequest, TrendsResponse
from ..services.langchain_trends_service import langchain_trends_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["trends"])

@router.post("/extract-trends", response_model=TrendsResponse)
async def extract_trends(req: TrendsRequest):
    """Extract trending topics from RSS feed using improved semantic clustering"""
    try:
        logger.info(f"Extracting trends for query: {req.query}")
        
        # Use LangChain-based service for better semantic understanding
        topics = langchain_trends_service.extract_trending_topics(
            feed_url=req.feed_url,
            max_articles=req.max_articles,
            min_frequency=req.min_frequency
        )
        
        return TrendsResponse(
            query=req.query,
            feed_url=req.feed_url,
            trends=topics,
            total_articles_processed=min(req.max_articles, len(topics) * 5)  # Estimate based on clusters
        )
    
    except Exception as e:
        logger.error(f"Error extracting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 