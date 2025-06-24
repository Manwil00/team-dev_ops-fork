from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.schemas import EmbedRequest, EmbedResponse, BatchEmbedRequest, BatchEmbedResponse
from ..services.embedding_service import embedding_service
from typing import List

router = APIRouter(prefix="", tags=["embedding"])

@router.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """Generate embedding for a single text"""
    try:
        vector = await embedding_service.embed_text(request.text)
        return EmbedResponse(vector=vector)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")

@router.post("/embed-batch", response_model=BatchEmbedResponse)
async def embed_batch(request: BatchEmbedRequest):
    """Generate embeddings for multiple texts with ChromaDB caching"""
    try:
        result = await embedding_service.embed_batch_with_cache(request.texts, request.ids)
        return BatchEmbedResponse(
            vectors=result["vectors"],
            cached_count=result["cached_count"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate batch embeddings: {str(e)}")

class EmbeddingsByIdsRequest(BaseModel):
    ids: List[str]

class EmbeddingsByIdsResponse(BaseModel):
    embeddings: List[List[float]]
    found_count: int

@router.post("/embeddings-by-ids", response_model=EmbeddingsByIdsResponse)
async def get_embeddings_by_ids(request: EmbeddingsByIdsRequest):
    """Retrieve cached embeddings by IDs from ChromaDB"""
    try:
        result = await embedding_service.get_embeddings_by_ids(request.ids)
        return EmbeddingsByIdsResponse(
            embeddings=result["embeddings"],
            found_count=result["found_count"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve embeddings: {str(e)}") 