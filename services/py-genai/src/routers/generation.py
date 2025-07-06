import logging
import os
from fastapi import APIRouter, HTTPException
from niche_explorer_models.models.generate_text_request import GenerateTextRequest
from niche_explorer_models.models.generate_text_response import GenerateTextResponse
from ..services.google_client import google_client
from ..services.openweb_client import OpenWebClient
from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AI"])

# Initialize clients
openweb_client = OpenWebClient()

# Determine which client to use based on environment variables
use_openweb = os.getenv("CHAIR_API_KEY") is not None
if use_openweb:
    logger.info("CHAIR_API_KEY found, using OpenWebUI for text generation.")
else:
    logger.info("CHAIR_API_KEY not found, using Google Gemini for text generation.")


@router.post("/generate/text", response_model=GenerateTextResponse)
async def generate_text(request: GenerateTextRequest):
    """
    Takes a prompt and returns a generated text from a specified Large Language Model.
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": "Prompt cannot be empty"},
        )

    model_to_use = request.model
    client_name = "OpenWebUI" if use_openweb else "Google Gemini"

    logger.info(
        f"Received generate text request for model '{model_to_use}' via {client_name}"
    )

    if use_openweb:
        generated_text = openweb_client.generate_text(
            prompt=request.prompt,
            model_name=model_to_use,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        # OpenWebClient's LLM has a default model if none is provided
        model_returned = model_to_use or openweb_client.llm.model_name
    else:
        generated_text = google_client.generate_text(
            prompt=request.prompt,
            model_name=model_to_use or settings.GENERATION_MODEL,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        model_returned = model_to_use or settings.GENERATION_MODEL

    return GenerateTextResponse(
        text=generated_text,
        model=model_returned,
        prompt=request.prompt,
    )
