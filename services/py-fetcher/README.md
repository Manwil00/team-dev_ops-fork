# Article Fetcher Service

This microservice fetches articles from external sources (arXiv and Reddit) and returns them in a normalized JSON format suitable for embedding.

## API Documentation

For detailed endpoints and specs, see the [Swagger Docs](https://aet-devops25.github.io/team-dev_ops/swagger/).

This service provides an endpoint to fetch and normalize articles from sources like arXiv and Reddit.

## Running Locally

```bash
cd services/py-fetcher
uvicorn src.main:app --reload --port 8200
```

The service runs on port 8200 in the Docker compose network.

## Tests

- Unit tests in tests/unit/  
- Integration tests in tests/integration/  
- Pact provider tests in tests/pact/
