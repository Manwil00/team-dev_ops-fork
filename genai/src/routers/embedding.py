from fastapi import APIRouter
from ..models.schemas import EmbedRequest, EmbedResponse
from ..services.embedding_service import embedding_service

router = APIRouter(prefix="", tags=["embedding"])

@router.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """Generate vector embedding for text"""
    vector = embedding_service.embed_text(request.text)
    return EmbedResponse(vector=vector) 