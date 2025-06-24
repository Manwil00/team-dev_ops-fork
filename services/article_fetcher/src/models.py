from pydantic import BaseModel
from typing import List, Optional

class FetchRequest(BaseModel):
    query: str  # subreddit name or arXiv category/search
    max_results: int = 50
    source_type: str  # 'research' | 'community'

class Article(BaseModel):
    id: str
    title: str
    link: str
    abstract: Optional[str] = None
    authors: Optional[List[str]] = None

class FetchResponse(BaseModel):
    articles: List[Article]
    total_found: int 