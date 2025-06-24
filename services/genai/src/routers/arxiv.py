from fastapi import APIRouter, HTTPException
from typing import Dict, List
from pydantic import BaseModel
from ..services.arxiv_service import arxiv_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/arxiv", tags=["arxiv"])

class AdvancedQueryRequest(BaseModel):
    search_terms: str
    category: str

class AdvancedQueryResponse(BaseModel):
    query: str
    description: str

class SearchRequest(BaseModel):
    query: str
    max_results: int = 50

class Article(BaseModel):
    id: str
    title: str
    link: str
    abstract: str
    authors: List[str]

class SearchResponse(BaseModel):
    articles: List[Article]
    total_found: int

@router.get("/categories")
async def get_arxiv_categories() -> Dict[str, List[str]]:
    """Get available ArXiv categories organized by field"""
    try:
        return arxiv_service.get_category_suggestions()
    except Exception as e:
        logger.error(f"Error getting ArXiv categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/build-query", response_model=AdvancedQueryResponse)
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

@router.post("/search", response_model=SearchResponse)
async def search_arxiv(req: SearchRequest):
    """Search arXiv papers by category or query"""
    try:
        articles = await arxiv_service.search_papers(req.query, req.max_results)
        
        return SearchResponse(
            articles=articles,
            total_found=len(articles)
        )
    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 