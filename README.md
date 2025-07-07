# NicheExplorer

An AI-powered research trend analysis platform that transforms research questions into comprehensive trend reports through automated content discovery and analysis.

## Overview

NicheExplorer is a microservices-based application that leverages machine learning and natural language processing to identify emerging trends in research domains. The system automatically fetches content from multiple sources, performs semantic analysis, and generates insightful reports.

**Core Components:**
- **Web Client** – Modern React frontend with TypeScript (port 80)
- **API Server** – Spring Boot orchestration layer (port 8080)
- **GenAI Service** – FastAPI service handling Google Gemini embeddings and Open Web Client classification (port 8000)
- **Topic Discovery** – Python microservice for content clustering and topic extraction (port 8100)
- **Article Fetcher** – Python microservice for RSS feed processing and content retrieval (port 8200)
- **Database** – PostgreSQL with pgvector extension for vector similarity search (port 5432)

## Architecture

| Service | Technology Stack | Port | Purpose |
|---------|------------------|------|---------|
| client | React + Vite + Nginx | 80 | User interface and interaction |
| api-server | Spring Boot + Java | 8080 | Request orchestration and business logic |
| genai | FastAPI + Python | 8000 | AI/ML processing and embeddings |
| topic-discovery | FastAPI + Python | 8100 | Content clustering and topic analysis |
| article-fetcher | FastAPI + Python | 8200 | Content retrieval and RSS processing |
| db | PostgreSQL + pgvector | 5432 | Data persistence and vector search |

## Quick Start

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/team-dev_ops.git
cd team-dev_ops

# Configure environment
cp .env.example .env

# Generate OpenAPI client libraries
bash api/scripts/gen-all.sh

# Local development (uses override with hard-coded localhost rules)
docker compose --env-file ./.env -f infra/docker-compose.yml -f infra/docker-compose.override.yml up --build -d

# Server / production deployment
docker compose --env-file ./.env -f infra/docker-compose.yml up --build -d

Access the application at: http://localhost
Traefik dashboard: http://localhost:8080/dashboard/

## API Documentation

The complete REST API specification is available in `api/openapi.yaml` and published automatically via GitHub Pages:

| Format | Live link |
| ------ | --------- |
| ReDoc  | https://AET-DevOps25.github.io/team-dev_ops/api.html |
| Swagger UI | https://AET-DevOps25.github.io/team-dev_ops/swagger/ |

You can still view the raw YAML locally or import it into tools like Postman, but the hosted docs stay up-to-date on every push.

## Development Workflow

### Modifying the API Schema

When updating the OpenAPI specification:

1. **Validate the schema:**
   ```bash
   pre-commit run -a
   ```
   *Note: Install pre-commit hooks once with `pip install pre-commit && pre-commit install`*

2. **Regenerate client libraries:**
   ```bash
   bash api/scripts/gen-all.sh
   ```

3. **Commit changes:**
   ```bash
   git add .
   git commit -m "Update API schema and regenerate clients"
   ```

4. **Rebuild containers:**
   ```bash
   docker compose -f infra/docker-compose.yml up --build
   ```

### Code Generation

Generated code is version-controlled in `generated/` directories. Docker images install this pre-generated code rather than generating it at build time, ensuring:
- Faster container builds
- Consistent client libraries across environments
- Offline development capability

# Automatic API documentation

The OpenAPI specification (`api/openapi.yaml`) is automatically rendered to static HTML using **ReDoc** and bundled Swagger UI:

| Format | URL |
| ------ | --- |
| ReDoc  | https://AET-DevOps25.github.io/team-dev_ops/api.html |
| Swagger UI | https://AET-DevOps25.github.io/team-dev_ops/swagger/ |

The `docs` GitHub Pages site is built by the workflow in `.github/workflows/docs.yml` every time `api/openapi.yaml` changes (or when you trigger the workflow manually).  Behind the scenes the job:

1. Installs `redoc-cli` and `swagger-ui-dist`
2. Generates `docs/api.html` (ReDoc)
3. Copies Swagger UI into `docs/swagger/` and points it to the local spec
4. Uploads the folder as a Pages artifact which the **Deploy Pages** action publishes

### View locally

```bash
# Install once
npm i -g redoc-cli swagger-ui-dist http-server

# Generate docs
redoc-cli bundle api/openapi.yaml -o docs/api.html

# Serve locally at http://localhost:8088
http-server docs -p 8088
```

### Trigger a fresh build

If you need to regenerate the published docs without touching the spec, push an empty commit:

```bash
git commit --allow-empty -m "docs: trigger Pages build"
git push origin main
```

> **Tip** – GitHub caches Pages aggressively. If you don't see new content, hard-refresh (Ctrl + Shift + R) or append `?t=$(date +%s)` to the URL.

---


```
team-dev_ops/
├── api/                    # OpenAPI specification and generators
├── services/               # Microservices source code
│   ├── py-genai/          # AI/ML service
│   ├── py-topics/         # Topic discovery service
│   ├── py-fetcher/        # Content fetching service
│   └── spring-api/        # Main API orchestrator
├── web-client/            # React frontend application
├── infra/                 # Infrastructure as code
│   ├── docker-compose.yml # Local development
│   ├── helm/              # Kubernetes charts
│   ├── terraform/         # Cloud infrastructure
│   └── ansible/           # Configuration management
└── docs/                  # Documentation and architecture
```


### Database Schema

The application uses PostgreSQL with pgvector extension for vector similarity search. Key tables:

**Core Tables:**
```sql
-- Analysis sessions
analysis (
    id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    type VARCHAR(50),   -- 'Research' or 'Community'
    feed_url TEXT NOT NULL,
    total_articles_processed INT,
    created_at TIMESTAMP
)

-- Discovered topics (one row per semantic cluster)
topic (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analysis(id),
    title TEXT NOT NULL,
    description TEXT,
    article_count INT,
    relevance INT,
    embedding vector(768),  -- Google Gemini embeddings
    created_at TIMESTAMP
)

-- Individual articles (deduplicated by external_id)
article (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analysis(id),
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    snippet TEXT,
    content_hash VARCHAR(64),  -- SHA-256 for extra safety
    embedding vector(768),
    created_at TIMESTAMP,
    UNIQUE (analysis_id, external_id)  -- no duplicate arXiv IDs per analysis
)

-- Many-to-many link between topics ↔ articles
topic_article (
    topic_id   UUID REFERENCES topic(id),
    article_id UUID REFERENCES article(id),
    PRIMARY KEY (topic_id, article_id)
)
```

**Vector Search Indexes:**
* `topic_embedding_idx`   – IVFFlat index for fast topic similarity search
* `article_embedding_idx` – IVFFlat index for article similarity search

Complete DDL: `services/spring-api/src/main/resources/db/migration/V1__unified_database_schema.sql`

