# Frame taken from in-class exercise: https://github.com/AET-DevOps25/w07-template completed with given solution
# https://gist.github.com/robertjndw/92f7b1a5a8818e0244fa99f4f6069b39

import os
import logging
import requests
import json
from typing import Any, List, Optional
from langchain.llms.base import LLM
from langchain_core.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManagerForLLMRun
from niche_explorer_models.models.classify_response import ClassifyResponse
from fastapi import HTTPException

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model_name,
            "messages": messages,
        }

        # Add any additional generation parameters from the call
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        if "model" in kwargs:
            payload["model"] = kwargs["model"]

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=30
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
            template="""You are an assistant that classifies user queries and selects the best content source.

Return ONLY valid JSON with keys 'source', 'feed', and optional 'confidence'. **No markdown fences**.

- source: 'arxiv' or 'reddit'
- feed  :
   * arxiv  → either a simple category (cs.CV, cs.AI, cs.LG …) **or** an advanced query string accepted by the arXiv export API (e.g. `all:"graph neural network"+AND+cat:cs.CV`).
   * reddit → subreddit name (MachineLearning, computervision …).

When you build an advanced arXiv query:
• Ignore generic stop-words such as: current, latest, recent, research, study, studies, trend, trends, paper, papers.
• Quote multi-word key phrases inside `all:"…"`.
• Combine multiple key phrases with `+AND+` and always keep a `cat:<category>` filter.

Examples (JSON output):
"computer vision trends"               → {{"source":"arxiv","feed":"cs.CV"}}
"graph neural networks in computer vision" → {{"source":"arxiv","feed":"all:graph+neural+network+AND+cat:cs.CV"}}
"GPU buying advice"                    → {{"source":"reddit","feed":"hardware"}}

User query: {query}""",
        )
        self.chain = self.prompt | self.llm

    def invoke(self, input: str, **kwargs: Any) -> str:
        return self._call(input, **kwargs)

    def classify_source(self, query: str) -> ClassifyResponse:
        try:
            logger.info("Using OpenWebUI for classification")

            output = self.chain.invoke({"query": query})

            # Strip markdown formatting if present
            if output.startswith("```"):
                output = output.strip().strip("```json").strip("```").strip()

            # Parse the JSON response
            data = json.loads(output)

            # Accept either new style ('feed') or legacy ('suggested_category')
            suggested_cat = data.get("feed") or data.get("suggested_category", "cs.CV")

            # Normalize shorthand
            if suggested_cat.strip().lower() in {"cv", "computer vision"}:
                suggested_cat = "cs.CV"

            return ClassifyResponse(
                source=data.get("source", "arxiv"),
                source_type="research"
                if data.get("source", "arxiv") == "arxiv"
                else "community",
                suggested_category=suggested_cat,
                confidence=data.get("confidence", 0.8),
            )

        except Exception as e:
            logger.error(
                f"Failed to classify query: {e}, falling back to default values."
            )
            return ClassifyResponse(
                source="arxiv",
                source_type="research",
                suggested_category="cs.CV",
                confidence=0.5,
            )

    def generate_text(
        self, prompt: str, model_name: str, max_tokens: int, temperature: float
    ) -> str:
        """Generates text using the OpenWebUI LLM."""
        try:
            effective_model = model_name or self.llm.model_name
            logger.info(
                f"Using OpenWebUI for text generation with model {effective_model}"
            )

            params = {}
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if model_name:
                params["model"] = model_name

            response = self.llm(prompt, **params)
            return response
        except Exception as e:
            logger.error(f"Failed to generate text with OpenWebUI: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"code": "GENERATION_ERROR", "message": str(e)},
            ) from e
