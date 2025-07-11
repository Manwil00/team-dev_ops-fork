import os

from fastapi import FastAPI
from .routers import classification, embedding, arxiv, generation
from starlette_prometheus import metrics, PrometheusMiddleware

# Check if the key exists. If not, raise an error to stop the app.
if not os.getenv("CHAIR_API_KEY"):
    raise ValueError("FATAL ERROR: The CHAIR_API_KEY environment variable is not set.")

# Check if the key exists. If not, raise an error to stop the app.
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("FATAL ERROR: The GOOGLE_API_KEY environment variable is not set.")


# Initialize FastAPI app with metadata matching OpenAPI spec
app = FastAPI(
    title="NicheExplorer GenAI Service",
    version="1.0.0",
    description="Microservice for GenAI tasks like classification and query generation.",
)

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)

# Include routers
app.include_router(classification.router, prefix="/api/v1")
app.include_router(embedding.router, prefix="/api/v1")
app.include_router(arxiv.router, prefix="/api/v1")
app.include_router(generation.router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
