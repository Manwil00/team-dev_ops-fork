from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TrendsRequest(BaseModel):
    query: str
    feed_url: Optional[str] = None  # Not used, but Java sends it
    max_articles: int = 50
    min_frequency: Optional[int] = 3  # Map to min_cluster_size

class TrendsRequestWithKeys(BaseModel):
    """API-first approach: receive pre-fetched article keys"""
    query: str
    article_keys: List[str]  # arXiv IDs or other document keys
    articles: List[Dict[str, Any]]  # Article metadata (title, link, etc.)
    min_cluster_size: int = 3

class TrendTopic(BaseModel):
    id: str  # Java expects string
    title: str
    description: str  # Java expects description field
    article_count: int
    relevance: int  # Java expects relevance (not confidence)
    articles: List[Dict[str, Any]]

class TrendsResponse(BaseModel):
    query: str
    feed_url: Optional[str] = None  # Java expects this field
    trends: List[TrendTopic]  # Java expects "trends" not "topics"
    total_articles_processed: int  # Java expects this field name 