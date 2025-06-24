import logging

from fastapi import APIRouter
from ..models.schemas import ClassifyRequest, ClassifyResponse
from ..services.openweb_client import OpenWebClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["classification"])
openweb_client = OpenWebClient()

@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """Classify query to determine research vs community source"""
    response = openweb_client.classify_source(request.query)
    logger.info(f"Parsed classification data: {response.source=}, {response.feed=}")
    return response