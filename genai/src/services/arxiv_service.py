"""
ArXiv API service for fetching research articles.
Supports both simple category searches and advanced query syntax.
"""

import arxiv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ArXivService:
    """
    Service for fetching articles from ArXiv using their API.
    
    Supports:
    1. Simple category searches: cs.CV, cs.AI, etc.
    2. Advanced query searches: all:"graph neural network"+AND+cat:cs.CV
    3. Keyword-based searches with category filtering
    """
    
    def __init__(self):
        self.client = arxiv.Client()
    
    def fetch_articles(self, query_or_category: str, max_articles: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch articles from ArXiv based on query or category.
        
        Args:
            query_or_category: Can be:
                - Simple category: "cs.CV", "cs.AI"
                - Advanced query: 'all:"graph neural network"+AND+cat:cs.CV'
                - User query that needs to be converted: "current trends in AI research"
            max_articles: Maximum number of articles to fetch
            
        Returns:
            List of article dictionaries with standardized fields
        """
        try:
            # Determine if this is a category, advanced query, or needs conversion
            search_query = self._build_search_query(query_or_category)
            
            logger.info(f"Fetching articles with ArXiv query: {search_query}")
            
            # Create ArXiv search
            search = arxiv.Search(
                query=search_query,
                max_results=max_articles,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            articles = []
            for result in self.client.results(search):
                article = {
                    'title': result.title,
                    'link': result.entry_id,
                    'summary': result.summary,
                    'description': result.summary,  # Alias for compatibility
                    'published': result.published.isoformat() if result.published else '',
                    'author': ', '.join([author.name for author in result.authors]) if result.authors else '',
                    'categories': [cat for cat in result.categories],
                    'pdf_url': result.pdf_url,
                    'doi': result.doi
                }
                articles.append(article)
            
            logger.info(f"Successfully fetched {len(articles)} articles from ArXiv")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching ArXiv articles: {e}")
            return []
    
    def _build_search_query(self, input_query: str) -> str:
        """
        Build appropriate ArXiv search query from input.
        
        Handles:
        1. Simple categories: cs.CV -> cat:cs.CV
        2. Advanced queries: already formatted -> use as-is
        3. Natural language: convert to searchable query
        """
        
        # If it's already an advanced query (contains operators), use as-is
        if self._is_advanced_query(input_query):
            return input_query
        
        # If it's a simple category, convert to category search
        if self._is_simple_category(input_query):
            return f"cat:{input_query}"
        
        # If it contains a category with additional terms, build combined query
        category_match = re.search(r'\b(cs\.[A-Z]{2}|math\.[A-Z]{2}|physics\.[a-z-]+)\b', input_query)
        if category_match:
            category = category_match.group(1)
            # Extract meaningful terms excluding the category
            terms = re.sub(r'\b(cs\.[A-Z]{2}|math\.[A-Z]{2}|physics\.[a-z-]+)\b', '', input_query)
            terms = self._extract_search_terms(terms.strip())
            if terms:
                return f'all:"{terms}"+AND+cat:{category}'
            else:
                return f"cat:{category}"
        
        # For natural language queries, try to map to appropriate categories and extract keywords
        return self._convert_natural_language_query(input_query)
    
    def _is_advanced_query(self, query: str) -> bool:
        """Check if query contains ArXiv advanced search operators"""
        advanced_operators = ['+AND+', '+OR+', 'all:', 'ti:', 'au:', 'abs:', 'cat:', 'co:']
        return any(op in query for op in advanced_operators)
    
    def _is_simple_category(self, query: str) -> bool:
        """Check if query is a simple category like cs.CV"""
        return bool(re.match(r'^[a-z]+\.[A-Z]{2,}$', query.strip()))
    
    def _extract_search_terms(self, text: str) -> str:
        """Extract meaningful search terms from text"""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        meaningful_words = [w for w in words if w not in stop_words]
        return ' '.join(meaningful_words[:5])  # Limit to 5 most relevant terms
    
    def _convert_natural_language_query(self, query: str) -> str:
        """
        Convert natural language query to ArXiv search.
        Maps common research areas to appropriate categories.
        """
        query_lower = query.lower()
        
        # Map query terms to ArXiv categories
        category_mappings = {
            'computer vision': 'cs.CV',
            'vision': 'cs.CV',
            'image': 'cs.CV',
            'artificial intelligence': 'cs.AI',
            'ai research': 'cs.AI',
            'machine learning': 'cs.LG',
            'deep learning': 'cs.LG',
            'neural network': 'cs.LG',
            'natural language': 'cs.CL',
            'nlp': 'cs.CL',
            'robotics': 'cs.RO',
            'human computer': 'cs.HC',
            'graphics': 'cs.GR',
            'information retrieval': 'cs.IR',
            'cryptography': 'cs.CR',
            'software engineering': 'cs.SE',
            'databases': 'cs.DB'
        }
        
        # Find the best matching category
        best_category = 'cs.AI'  # Default fallback
        for term, category in category_mappings.items():
            if term in query_lower:
                best_category = category
                break
        
        # Extract key terms from the query
        search_terms = self._extract_search_terms(query)
        
        if search_terms:
            return f'all:"{search_terms}"+AND+cat:{best_category}'
        else:
            return f"cat:{best_category}"
    
    def build_advanced_query(self, search_terms: str, category: str) -> str:
        """
        Build an advanced ArXiv query combining search terms and category.
        
        Example: build_advanced_query("graph neural network", "cs.CV")
        Returns: 'all:"graph neural network"+AND+cat:cs.CV'
        """
        if not search_terms.strip():
            return f"cat:{category}"
        
        # Clean and format search terms
        cleaned_terms = self._extract_search_terms(search_terms)
        return f'all:"{cleaned_terms}"+AND+cat:{category}'
    
    def get_category_suggestions(self) -> Dict[str, List[str]]:
        """Return common ArXiv categories organized by field"""
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
                "cs.DB - Databases"
            ],
            "Mathematics": [
                "math.ST - Statistics Theory",
                "math.OC - Optimization and Control",
                "math.PR - Probability",
                "math.NA - Numerical Analysis"
            ],
            "Physics": [
                "physics.data-an - Data Analysis, Statistics and Probability",
                "physics.comp-ph - Computational Physics"
            ]
        }

# Create service instance
arxiv_service = ArXivService() 