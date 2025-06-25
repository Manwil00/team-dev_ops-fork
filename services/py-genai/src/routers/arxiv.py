from fastapi import APIRouter, HTTPException
from typing import Dict, List
from pydantic import BaseModel
from ..services.query_generation_service import query_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/arxiv", tags=["arxiv"])

class AdvancedQueryRequest(BaseModel):
    search_terms: str
    category: str

class AdvancedQueryResponse(BaseModel):
    query: str
    description: str

@router.get("/categories")
async def get_arxiv_categories() -> Dict[str, List[str]]:
    """Get available ArXiv categories organized by field"""
    try:
        return query_service.get_category_suggestions()
    except Exception as e:
        logger.error(f"Error getting ArXiv categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/build-query", response_model=AdvancedQueryResponse)
async def build_advanced_query(req: AdvancedQueryRequest):
    """Build an advanced ArXiv query from search terms and category"""
    try:
        query = query_service.build_advanced_query(req.search_terms, req.category)
        description = f"Search for '{req.search_terms}' in {req.category} category"
        
        return AdvancedQueryResponse(
            query=query,
            description=description
        )
    except Exception as e:
        logger.error(f"Error building advanced query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoint is now handled by the separate article-fetcher service. 