from fastapi import FastAPI
from .routers import classification, embedding, arxiv

# Initialize FastAPI app with metadata matching OpenAPI spec
app = FastAPI(
    title="NicheExplorer GenAI Service",
    version="2.2.0",
    description="Microservice for GenAI tasks like classification and query generation."
)

# Include routers
app.include_router(classification.router, prefix="/api/v1")
app.include_router(embedding.router, prefix="/api/v1")
app.include_router(arxiv.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "NicheExplorer GenAI Service is running", "version": "2.2.0"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
