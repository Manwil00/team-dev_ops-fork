from fastapi import APIRouter
from ..models.schemas import ClassifyRequest, ClassifyResponse
from ..services.google_client import google_client

router = APIRouter(prefix="", tags=["classification"])

@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """Classify query to determine research vs community source"""
    source, feed = google_client.classify_source(request.query)
    return ClassifyResponse(source=source, feed=feed) 