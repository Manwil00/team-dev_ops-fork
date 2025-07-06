import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query
from niche_explorer_models.models.embedding_request import EmbeddingRequest
from niche_explorer_models.models.embedding_response import EmbeddingResponse
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AI"])
embedding_service = EmbeddingService()


@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """Generate embeddings for multiple texts with ChromaDB caching"""
    if len(request.texts) != len(request.ids):
        raise HTTPException(
            status_code=400, detail="The number of texts and ids must be the same."
        )
    try:
        logger.info(f"Received embedding request for {len(request.texts)} texts")
        result = await embedding_service.embed_batch_with_cache(
            request.texts, request.ids
        )

        return EmbeddingResponse(
            embeddings=result["vectors"], cached_count=result["cached_count"]
        )
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate embeddings: {str(e)}"
        )


@router.get("/embeddings", response_model=EmbeddingResponse)
async def get_embeddings(
    ids: List[str] = Query(..., description="Document IDs to retrieve embeddings for")
):
    """Retrieve cached embeddings by document IDs"""
    try:
        logger.info(f"Retrieving embeddings for {len(ids)} document IDs")
        result = await embedding_service.get_embeddings_by_ids(ids)

        return EmbeddingResponse(
            embeddings=result["embeddings"], found_count=result["found_count"]
        )
    except Exception as e:
        logger.error(f"Failed to retrieve embeddings: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve embeddings: {str(e)}"
        )
