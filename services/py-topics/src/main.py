from fastapi import FastAPI, HTTPException
from niche_explorer_models.models.topic_discovery_request import TopicDiscoveryRequest
from niche_explorer_models.models.topic_discovery_response import TopicDiscoveryResponse
from niche_explorer_models.models.article import Article
from .services.topic_service import topic_service
import logging
import os

# Configure root logging level from environment variable (default INFO)
numeric_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=numeric_level)

logger = logging.getLogger("topic_discovery")

# Initialize FastAPI app with metadata matching OpenAPI spec
app = FastAPI(
    title="NicheExplorer Topic Discovery Service",
    version="1.0.0",
    description="Discovers topics from article collections using ML clustering"
)

@app.post("/api/v1/topics/discover", response_model=TopicDiscoveryResponse)
async def discover_topics(request: TopicDiscoveryRequest):
    """Perform topic discovery on a collection of articles"""
    try:
        logger.info(f"Received topic discovery request: query='{request.query}', {len(request.articles)} articles")
        
        # Use min_cluster_size from request or default
        min_cluster_size = getattr(request, 'min_cluster_size', 2) or 2
        
        # Discover topics using the service
        result = await topic_service.discover_topic(
            query=request.query,
            article_keys=request.article_ids,
            articles=request.articles,
            min_cluster_size=min_cluster_size
        )
        
        logger.info(f"Successfully discovered topics")
        return result
        
    except Exception as e:
        logger.error(f"Failed to discover topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to discover topics: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
