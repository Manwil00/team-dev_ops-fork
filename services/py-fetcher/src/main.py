from fastapi import FastAPI, HTTPException
from .models import FetchRequest, FetchResponse, Article
import logging
from .services.arxiv_service import arxiv_fetcher
from .services.reddit_service import reddit_fetcher

logger = logging.getLogger("article_fetcher")

app = FastAPI(title="Article Fetcher Service", version="0.1.0")

@app.post("/fetch", response_model=FetchResponse)
async def fetch_articles(req: FetchRequest):
    if req.source_type == "research":
        articles = await arxiv_fetcher.fetch(req.query, req.max_results)
    elif req.source_type == "community":
        articles = await reddit_fetcher.fetch(req.query, req.max_results)
    else:
        raise HTTPException(status_code=400, detail="Invalid source_type")

    return FetchResponse(articles=articles, total_found=len(articles))

@app.get("/")
async def root():
    return {"service": "article-fetcher", "status": "ok"} 