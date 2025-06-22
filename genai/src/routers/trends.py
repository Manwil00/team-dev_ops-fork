from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, List
from pydantic import BaseModel
from ..models.schemas import TrendsRequest, TrendsResponse
from ..services.langchain_trends_service import langchain_trends_service
from ..services.arxiv_service import arxiv_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["trends"])

class AdvancedQueryRequest(BaseModel):
    search_terms: str
    category: str

class AdvancedQueryResponse(BaseModel):
    query: str
    description: str

@router.post("/extract-trends", response_model=TrendsResponse)
async def extract_trends(req: TrendsRequest):
    """Extract trending topics using ArXiv API with improved semantic clustering"""
    try:
        logger.info(f"Extracting trends for query: {req.query}")
        
        # Use LangChain-based service with ArXiv API integration
        topics = langchain_trends_service.extract_trending_topics(
            query_or_feed=req.feed_url,  # This can now be ArXiv query, category, or RSS URL
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

@router.get("/arxiv-categories")
async def get_arxiv_categories() -> Dict[str, List[str]]:
    """Get available ArXiv categories organized by field"""
    try:
        return arxiv_service.get_category_suggestions()
    except Exception as e:
        logger.error(f"Error getting ArXiv categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/build-advanced-query", response_model=AdvancedQueryResponse)
async def build_advanced_query(req: AdvancedQueryRequest):
    """Build an advanced ArXiv query from search terms and category"""
    try:
        query = arxiv_service.build_advanced_query(req.search_terms, req.category)
        description = f"Search for '{req.search_terms}' in {req.category} category"
        
        return AdvancedQueryResponse(
            query=query,
            description=description
        )
    except Exception as e:
        logger.error(f"Error building advanced query: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 