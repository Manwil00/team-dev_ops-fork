# Topic Discovery Service

This microservice performs semantic clustering on embeddings using HDBSCAN and generates topic labels.

## Responsibilities
- Fetch embeddings for articles from GenAI service (caching fallback via POST if needed).
- Use BERTopic (with UMAP dimensionality reduction and HDBSCAN clustering) to model topics from embeddings and document texts.
- For large clusters (&gt;10 articles), perform hierarchical sub-clustering with another BERTopic pass.
- Generate topic labels (5-word titles) and descriptions (2-sentence summaries) using LLM prompts via GenAI service.
- Compute relevance scores based on cluster sizes and sort topics accordingly.

## API Documentation

For detailed endpoints and specs, see the [Swagger Docs](https://aet-devops25.github.io/team-dev_ops/swagger/).

This service provides an endpoint for discovering and labeling topics from article embeddings via clustering.

## Configuration
Lightweight, uses scikit-learn, HDBSCAN, UMAP.

## Running Locally
Run `uvicorn src.main:app --reload` from the directory.

## Tests
- Unit and integration tests in tests/.

Service structure:
```
src/
├── main.py
└── services/
    └── topic_service.py
```
