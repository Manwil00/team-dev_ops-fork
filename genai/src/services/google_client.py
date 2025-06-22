import json
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai
from ..config.settings import settings

logger = logging.getLogger(__name__)

# Load .env file from the root directory (go up 3 levels from this file)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

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
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            return data.get("source", "research"), data.get("feed", "cs.CV")
        except Exception as e:
            logger.error("Failed to classify query: %s", e)
            return "research", "cs.CV"

# Singleton instance
google_client = GoogleGenAIClient() 