"""
QueryGenerationService – Offers utility functions to generate advanced arXiv search
queries and provide curated category suggestions.  It NO LONGER performs any HTTP
fetching itself – that responsibility has moved to the article-fetcher service.
"""

import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class QueryGenerationService:
    """Light-weight helper focused on the *generative* part of the GenAI layer.

    It converts free-form user text to valid arXiv API queries and exposes a
    curated list of common categories.  Network IO or data fetching is *out of
    scope* – see the dedicated `article-fetcher` micro-service for that.
    """

    # Public helpers ----------------------------------------------------------------
    def build_advanced_query(self, search_terms: str, category: str) -> str:
        """Return an advanced arXiv query like `all:"graph neural network"+AND+cat:cs.CV`."""
        if not search_terms.strip():
            return f"cat:{category}"

        cleaned_terms = self._extract_search_terms(search_terms)
        return f'all:"{cleaned_terms}"+AND+cat:{category}'

    def get_category_suggestions(self) -> Dict[str, List[str]]:
        """Hand-picked popular arXiv categories grouped by discipline."""
        return {
            "Computer Science": [
                "cs.AI - Artificial Intelligence",
                "cs.CV - Computer Vision and Pattern Recognition",
                "cs.LG - Machine Learning",
                "cs.CL - Computation and Language",
                "cs.RO - Robotics",
                "cs.HC - Human-Computer Interaction",
                "cs.GR - Graphics",
                "cs.IR - Information Retrieval",
                "cs.CR - Cryptography and Security",
                "cs.SE - Software Engineering",
                "cs.DB - Databases",
            ],
            "Mathematics": [
                "math.ST - Statistics Theory",
                "math.OC - Optimization and Control",
                "math.PR - Probability",
                "math.NA - Numerical Analysis",
            ],
            "Physics": [
                "physics.data-an - Data Analysis, Statistics and Probability",
                "physics.comp-ph - Computational Physics",
            ],
        }

    # ------------------------------------------------------------------------------
    # Internal helpers – kept *private* to avoid leaking complexity
    # ------------------------------------------------------------------------------
    def _build_search_query(self, input_query: str) -> str:
        """Translate free-form text or category to an arXiv query string."""
        if self._is_advanced_query(input_query):
            return input_query
        if self._is_simple_category(input_query):
            return f"cat:{input_query}"

        # Mixed phrase containing category?
        category_match = re.search(
            r"\b(cs\.[A-Z]{2}|math\.[A-Z]{2}|physics\.[a-z-]+)\b", input_query
        )
        if category_match:
            category = category_match.group(1)
            terms = re.sub(
                r"\b(cs\.[A-Z]{2}|math\.[A-Z]{2}|physics\.[a-z-]+)\b", "", input_query
            )
            terms = self._extract_search_terms(terms.strip())
            return f'all:"{terms}"+AND+cat:{category}' if terms else f"cat:{category}"

        # Fallback to natural-language heuristics
        return self._convert_natural_language_query(input_query)

    # ---------- regex / NLP helpers ------------------------------------------------
    def _is_advanced_query(self, query: str) -> bool:
        advanced_ops = ["+AND+", "+OR+", "all:", "ti:", "au:", "abs:", "cat:", "co:"]
        return any(op in query for op in advanced_ops)

    def _is_simple_category(self, query: str) -> bool:
        return bool(re.match(r"^[a-z]+\.[A-Z]{2,}$", query.strip()))

    def _extract_search_terms(self, text: str) -> str:
        stop_words = {
            "the",
            "and",
            "or",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        meaningful = [w for w in words if w not in stop_words]
        return " ".join(meaningful[:5])

    def _convert_natural_language_query(self, query: str) -> str:
        query_lower = query.lower()
        category_mappings = {
            "computer vision": "cs.CV",
            "vision": "cs.CV",
            "image": "cs.CV",
            "artificial intelligence": "cs.AI",
            "ai research": "cs.AI",
            "machine learning": "cs.LG",
            "deep learning": "cs.LG",
            "neural network": "cs.LG",
            "natural language": "cs.CL",
            "nlp": "cs.CL",
            "robotics": "cs.RO",
            "human computer": "cs.HC",
            "graphics": "cs.GR",
            "information retrieval": "cs.IR",
            "cryptography": "cs.CR",
            "software engineering": "cs.SE",
            "databases": "cs.DB",
        }
        best_category = "cs.AI"
        for term, category in category_mappings.items():
            if term in query_lower:
                best_category = category
                break
        search_terms = self._extract_search_terms(query)
        return (
            f'all:"{search_terms}"+AND+cat:{best_category}'
            if search_terms
            else f"cat:{best_category}"
        )


# Singleton – importable as `query_service`
query_service = QueryGenerationService()
