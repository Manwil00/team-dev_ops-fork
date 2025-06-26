import logging
from fastapi import APIRouter, HTTPException, Path, Body
from niche_explorer_models.models.query_builder_request import QueryBuilderRequest
from niche_explorer_models.models.query_builder_response import QueryBuilderResponse
from ..services.query_generation_service import query_service
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AI"])

@router.post("/query/build/{source}", response_model=None)
async def build_source_query(
    source: str = Path(..., description="Target data source"),
    payload: dict = Body(...)
):
    """Generate optimized query for a specific data source using AI"""
    try:
        # Parse incoming payload once
        req_obj = QueryBuilderRequest.from_dict(payload)

        if source.lower() == "arxiv":
            # Build arXiv query
            category = req_obj.filters.category if req_obj.filters and req_obj.filters.category else "cs.CV"
            query = query_service.build_advanced_query(req_obj.search_terms, category)
            description = f"Advanced arXiv search for '{req_obj.search_terms}' in category {category}"
        elif source.lower() == "reddit":
            # Build Reddit query (subreddit name)
            subreddit = req_obj.filters.subreddit if req_obj.filters and req_obj.filters.subreddit else "MachineLearning"
            query = subreddit
            description = f"Reddit search in r/{subreddit} for '{req_obj.search_terms}'"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")

        response_obj = QueryBuilderResponse(
            query=query,
            description=description,
            source=source.lower()
        )
        return JSONResponse(content=response_obj.to_dict())
    except Exception as e:
        logger.error(f"Failed to build query for source {source}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to build query: {str(e)}")

# Search endpoint is now handled by the separate article-fetcher service.
