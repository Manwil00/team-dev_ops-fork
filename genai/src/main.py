from fastapi import FastAPI
from .routers import classification, embedding, trends

# Initialize FastAPI app
app = FastAPI(title="GenAI API", version="1.0.0")

# Include routers
app.include_router(classification.router)
app.include_router(embedding.router)
app.include_router(trends.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "NicheExplorer GenAI Service is running", "version": "1.0"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"} 