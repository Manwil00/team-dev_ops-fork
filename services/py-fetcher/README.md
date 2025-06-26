# Article Fetcher Service

_Stub implementation_

This micro-service will be responsible for fetching raw articles/posts from
external sources (arXiv, Reddit, etc.) and returning them in a normalised JSON
schema suitable for embedding.

Routes (planned)
----------------
* **POST /fetch** – body: `{ query, max_results, source_type }`
  * `source_type = research` → query arXiv API
  * `source_type = community` → fetch subreddit RSS
* Future dedicated endpoints `/fetch/research`, `/fetch/community` for clarity.

Running locally
---------------
```bash
cd services/article_fetcher
uvicorn src.main:app --reload --port 8200
```

The Dockerfile is already configured; the service will start on port 8200 in
the compose network. Currently returns a stub response so that downstream
services can be developed in parallel.
