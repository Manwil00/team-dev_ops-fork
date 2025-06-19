# NicheExplorer

NicheExplorer is a micro-services platform that monitors research and community RSS feeds, groups related articles into topics, stores them with vector embeddings and serves them through a simple web interface.

---

## Architecture Overview

```
┌──────────────┐  HTTP  ┌──────────────┐  REST  ┌─────────────┐
│ React Client │ ─────▶ │ Spring Boot  │ ─────▶ │  GenAI      │
│  (port 80)   │        │  API Server  │        │  Service    │
└──────────────┘        │ (port 8080)  │        │ (port 8000) │
                        └──────┬──────┘        └────┬──────┘
                               │ JDBC                  │
                               ▼                      │
                        ┌──────────────┐             │
                        │ PostgreSQL + │◀────────────┘
                        │  pgvector    │
                        └──────────────┘
```

Component roles:
* **Frontend** – React + Vite SPA (client container)
* **API Server** – Spring Boot service that orchestrates the pipeline and persists data
* **GenAI Service** – FastAPI service that performs topic discovery & embeddings
* **Database** – PostgreSQL 15 with `pgvector` extension

---

## Processing Pipeline

1. **Query submission** – User enters a question, e.g. "current trends in computer vision".
2. **Feed selection** – API server determines the correct RSS feed (ArXiv or Reddit).
3. **Article harvesting** – GenAI service downloads up to *N* recent entries (default 50).
4. **Topic discovery** – Articles are grouped into topics (see next section).
5. **Storage** – Topics, articles and their 768-dimensional embeddings are stored in the database.
6. **Presentation** – Frontend displays ranked topics with relevance bars and expandable articles.

---

## Topic Discovery (exact implementation)

The algorithm implemented in `genai/src/services/langchain_trends_service.py` is deliberately lightweight while performance tuning is in progress:

1. **Keyword catalogue** – A predefined list of ML/AI terms such as *neural*, *vision*, *language*, *transformer*, *training* …
2. **Scanning** – Each article's title + summary is scanned for the first matching keyword.
3. **Grouping** – Articles are assigned to that keyword's bucket; if nothing matches, the first meaningful word of the title is used.
4. **Filtering** – Buckets with at least **two** articles become topics.
5. **Labelling** –
   * Title → "<keyword> Research"
   * Description → "Recent research advances in <keyword>"
6. **Relevance score** – `50 + min(article_count × 3, 50)` (range 50-100).
7. **Ranking** – Topics are sorted by relevance and article count; the six best are returned.

Note: More sophisticated DBSCAN-based semantic clustering utilities exist in the same file but are currently disabled.

---

## Database Schema (Flyway migration V1)

```sql
CREATE TABLE analysis (
    id          UUID PRIMARY KEY,
    query       TEXT      NOT NULL,
    timestamp   TIMESTAMPTZ DEFAULT NOW(),
    type        VARCHAR(50) NOT NULL,
    feed_url    TEXT
);

CREATE TABLE trend (
    id              UUID PRIMARY KEY,
    analysis_id     UUID REFERENCES analysis(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    relevance_score INTEGER CHECK (relevance_score BETWEEN 0 AND 100),
    article_count   INTEGER DEFAULT 0
);

CREATE TABLE article (
    id            UUID PRIMARY KEY,
    trend_id      UUID REFERENCES trend(id),
    title         TEXT NOT NULL,
    content       TEXT,
    link          TEXT UNIQUE,
    snippet       TEXT,
    content_hash  VARCHAR(64) UNIQUE,
    embedding     VECTOR(768),
    published_date TIMESTAMPTZ
);

CREATE INDEX article_embedding_idx ON article USING ivfflat (embedding vector_cosine_ops);
```

---

## Quick Start

1. Install Docker Desktop.
2. `git clone … && cd team-dev_ops`.
3. Create `.env` with `GOOGLE_API_KEY=<your key>` (required for embeddings on first run).
4. `docker-compose up -d` – starts **db**, **genai**, **api-server** and **client**.
5. Open <http://localhost> and run your first analysis.

---

## Roadmap

* Replace keyword grouping with true semantic clustering.
* Add scheduled background re-crawling.
* Deploy with the Helm chart inside `helm/`. 