import logging
from fastapi import APIRouter, HTTPException
from niche_explorer_models.models.classify_request import ClassifyRequest
from niche_explorer_models.models.classify_response import ClassifyResponse
from ..services.openweb_client import OpenWebClient
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AI"])
openweb_client = OpenWebClient()


@router.post("/classify", response_model=ClassifyResponse)
async def classify_query(request: ClassifyRequest):
    """Classify query to determine research vs community source"""
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": "Query cannot be empty"},
        )

    generic_words = r"\b(?:current|latest|recent|research|study|studies|trend|trends|paper|papers|growing|growth)\b"
    cleaned_query = re.sub(generic_words, "", request.query, flags=re.IGNORECASE)
    cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()

    logger.info(
        f"Received classify request: original='{request.query}', cleaned='{cleaned_query}'"
    )
    response = openweb_client.classify_source(cleaned_query or request.query)
    logger.info(
        f"Parsed classification data: {response.source=}, {response.suggested_category=}"
    )

    # Map source to source_type
    source_type = "research" if response.source == "arxiv" else "community"

    # Convert the attrs response to our Pydantic model
    return ClassifyResponse(
        source=response.source,
        source_type=source_type,
        suggested_category=response.suggested_category,
    )
