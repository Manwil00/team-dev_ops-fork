import json
import logging
import os
import google.generativeai as genai
from ..settings import settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY missing in .env")

# Configure genai client with newer API
genai.configure(api_key=GOOGLE_API_KEY)


class GoogleGenAIClient:
    def __init__(self):
        # No need to create client instance with new API
        pass

    def classify_source(self, query: str) -> tuple[str, str]:
        """Classify query to determine research or community source and generate appropriate feed identifier"""
        prompt = (
            "You are an assistant that classifies research queries and generates ArXiv search parameters.\n"
            "Return ONLY valid JSON with keys 'source' and 'feed'.\n"
            "- source: 'research' or 'community'.\n"
            "- feed: \n"
            "  * For research: arXiv category (e.g. cs.CV, cs.AI, cs.LG) OR advanced query (e.g. 'all:\"graph neural network\"+AND+cat:cs.CV')\n"
            "  * For community: subreddit name only (e.g. computervision)\n"
            "For research queries, prefer advanced ArXiv queries when specific terms are mentioned.\n"
            "Examples:\n"
            "- 'computer vision trends' -> cs.CV\n"
            "- 'graph neural networks in computer vision' -> 'all:\"graph neural network\"+AND+cat:cs.CV'\n"
            "- 'transformer architectures' -> 'all:\"transformer architecture\"+AND+cat:cs.LG'\n"
            f"User query: {query}"
        )

        try:
            model = genai.GenerativeModel(settings.GENERATION_MODEL)
            response = model.generate_content(
                prompt, generation_config=genai.types.GenerationConfig()
            )
            data = json.loads(response.text)
            return data.get("source", "research"), data.get("feed", "cs.CV")
        except Exception as e:
            logger.error("Failed to classify query: %s", e)
            return "research", "cs.CV"

    def generate_text(
        self, prompt: str, model_name: str, max_tokens: int, temperature: float
    ) -> str:
        """
        Generates text using the specified Google Generative AI model.

        Args:
            prompt: The prompt to send to the model.
            model_name: The name of the model to use (e.g., "gemini-pro").
            max_tokens: The maximum number of tokens to generate.
            temperature: The temperature for sampling.

        Returns:
            The generated text.
        """
        try:
            logger.info(
                f"Generating text with model '{model_name}' and prompt: {prompt[:100]}..."
            )
            model = genai.GenerativeModel(model_name or settings.GENERATION_MODEL)
            config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens, temperature=temperature
            )
            response = model.generate_content(prompt, generation_config=config)
            logger.info("Successfully generated text.")
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            raise HTTPException(
                status_code=500,
                detail={"code": "GENERATION_ERROR", "message": str(e)},
            ) from e


# Singleton instance
google_client = GoogleGenAIClient()
