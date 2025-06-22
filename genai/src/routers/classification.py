from fastapi import APIRouter
from ..models.schemas import ClassifyRequest, ClassifyResponse
from ..services.openweb_client import OpenWebClient

router = APIRouter(prefix="", tags=["classification"])
openweb_client = OpenWebClient()

@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """Classify query to determine research vs community source"""
    source, feed = openweb_client.classify_source(request.query)
    return ClassifyResponse(source=source, feed=feed)