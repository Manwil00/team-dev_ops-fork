# GenAI Service

This service handles query classification, ArXiv integration, embedding generation using Google Gemini or Sentence Transformers, and saving embeddings to our vector db.

## Responsibilities
- Classify queries to determine type (research/community) and ArXiv categories.
- Generate and cache semantic embeddings and store them.
- Generate optimized query for a specific data source using AI
- Takes a prompt and returns a generated text from a specified Large Language Model (e.g., Gemini, OpenRouter).

## API Documentation

For detailed endpoints and specs, see the [Swagger Docs](https://aet-devops25.github.io/team-dev_ops/swagger/).

This service provides endpoints for query classification, ArXiv integration, embedding generation/caching, and text generation.

## Configuration
- GOOGLE_API_KEY: For Gemini (falls back to local model if missing).
- CHAIR_API_KEY: For classification.

## Running Locally
Run `uvicorn src.main:app --reload` from the directory.

## Tests
- Unit, integration, and Pact tests in tests/.

Service structure:
```
src/
├── main.py
├── routers/
│   ├── arxiv.py
│   ├── classification.py
│   ├── embedding.py
│   └── generation.py
├── services/
│   ├── embedding_service.py
│   ├── google_client.py
│   ├── openweb_client.py
│   └── query_generation_service.py
└── settings/
```
