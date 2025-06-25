# Frame taken from in-class exercise: https://github.com/AET-DevOps25/w07-template completed with given solution 
# https://gist.github.com/robertjndw/92f7b1a5a8818e0244fa99f4f6069b39

import os
import logging
import requests
from typing import Any, List, Optional
from langchain.llms.base import LLM
from langchain_core.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManagerForLLMRun
from ..models.schemas import ClassifyResponse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the default source and feed for classification
DEFAULT_SOURCE = "research"
DEFAULT_FEED = "cs.CV"


# Environment configuration
CHAIR_API_KEY = os.getenv("CHAIR_API_KEY")
API_URL = "https://gpu.aet.cit.tum.de/api/chat/completions"

if not CHAIR_API_KEY:
    raise RuntimeError("CHAIR_API_KEY missing in .env")

class OpenWebUILLM(LLM):
    """
    Custom LangChain LLM wrapper for Open WebUI API.
    
    This class integrates the Open WebUI API with LangChain's LLM interface,
    allowing us to use the API in LangChain chains and pipelines.
    """
    
    api_url: str = API_URL
    api_key: str = CHAIR_API_KEY
    model_name: str = "llama3.3:latest"
    
    @property
    def _llm_type(self) -> str:
        return "open_webui"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call the Open WebUI API to generate a response.
        
        Args:
            prompt: The input prompt to send to the model
            stop: Optional list of stop sequences
            run_manager: Optional callback manager for LangChain
            **kwargs: Additional keyword arguments
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If API call fails
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Build messages for chat completion
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        payload = {
            "model": self.model_name,
            "messages": messages,
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            result = response.json()

            # Extract the response content
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                a = content.strip()
                return a
            else:
                raise ValueError("Unexpected response format from API")
                
        except requests.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except (KeyError, IndexError, ValueError) as e:
            raise Exception(f"Failed to parse API response: {str(e)}")

class OpenWebClient:
    def __init__(self):
        self.llm = OpenWebUILLM()
        self.prompt = PromptTemplate(
            input_variables=["query"],
            template="""You are an assistant that decides which single RSS feed to query.
            Return ONLY valid JSON with keys 'source' and 'feed'.
            - source: 'research' or 'community'.
            - feed: if research, give the arXiv subject ID only (e.g. cs.CV); if community, give the subreddit name only (e.g. computervision).
            User query: {query}"""
        )
        self.chain = self.prompt | self.llm

    def invoke(self, input: str, **kwargs: Any) -> str:
        return self._call(input, **kwargs)

    def classify_source(self, query: str) -> tuple[str, str]:
        try:
            logger.info("Using OpenWebUI for classification")
            
            output = self.chain.invoke({"query": query})

            # Strip markdown formatting if present
            if output.startswith("```"):
                output = output.strip().strip("```json").strip("```").strip()

            return ClassifyResponse.parse_raw(output)

        except Exception as e:
            logger.error(f"Failed to classify query: {e}, falling back to default source {DEFAULT_SOURCE} and feed {DEFAULT_FEED}.")
            return ClassifyResponse(source=DEFAULT_SOURCE, feed=DEFAULT_FEED)