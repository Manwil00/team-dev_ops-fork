import logging
from fastapi import APIRouter
from niche_explorer_models.models.classify_request import ClassifyRequest
from niche_explorer_models.models.classify_response import ClassifyResponse
from ..services.openweb_client import OpenWebClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AI"])
openweb_client = OpenWebClient()

@router.post("/classify", response_model=ClassifyResponse)
async def classify_query(request: ClassifyRequest):
    """Classify query to determine research vs community source"""
    logger.info(f"Received classify request: query='{request.query}'")
    response = openweb_client.classify_source(request.query)
    logger.info(f"Parsed classification data: {response.source=}, {response.suggested_category=}")
    
    # Map source to source_type
    source_type = "research" if response.source == "arxiv" else "community"
    
    # Convert the attrs response to our Pydantic model
    return ClassifyResponse(
        source=response.source,
        source_type=source_type,
        suggested_category=response.suggested_category
    )
