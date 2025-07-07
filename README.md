# NicheExplorer

[![CI](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/ci.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/ci.yml)
[![Docs](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/docs.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Docker](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/build_docker.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/build_docker.yml)
[![Deploy Helm](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/deploy_helm.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/deploy_helm.yml)
[![Manual Docker Deploy](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/deploy_docker_manual_input.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/deploy_docker_manual_input.yml)

**Catch emerging research trends in seconds.** Type a question, NicheExplorer fetches the latest papers & discussions, clusters them into semantic topics and presents an interactive report.

> 🌐 **Live demo:** _coming soon_ (TODO)

## Demo

> The GIF below shows a complete front-end flow: entering a query, running the pipeline, and browsing the discovered topics.

![NicheExplorer demo](docs/demo.gif)

---


# Quick Start

## Local Development Setup

#### 1. Clone repository & configure environment

```bash
git clone https://github.com/your-org/team-dev_ops.git
cd team-dev_ops

Configure environment
cp .env.example .env
```
#### 2.  Generate OpenAPI client libraries
```bash
bash api/scripts/gen-all.sh 
``` 

#### 3. Local development (uses override with hard-coded localhost rules)
```bash
docker compose --env-file ./.env -f infra/docker-compose.yml -f infra/docker-compose.override.yml up --build -d
```
#### (Optional) Server / production deployment
```bash
docker compose --env-file ./.env -f infra/docker-compose.yml up --build -d
```

## Overview

NicheExplorer is a microservices-based application that leverages machine learning and natural language processing to identify emerging trends in research domains. The system automatically fetches content from multiple sources, performs semantic analysis, and generates insightful reports.

| Service           | Technology Stack       | Port | Purpose                                   |
|------------------|------------------------|------|-------------------------------------------|
| client           | React + Vite + Nginx   | 80   | User interface and interaction            |
| api-server       | Spring Boot + Java     | 8080 | Request orchestration and business logic [[docs](services/spring-api/README.md)] |
| genai            | FastAPI + Python       | 8000 | AI/ML processing and embeddings [[docs](services/py-genai/README.md)] |
| topic-discovery  | FastAPI + Python       | 8100 | Content clustering and topic analysis [[docs](services/py-topics/README.md)] |
| article-fetcher  | FastAPI + Python       | 8200 | Content retrieval and RSS processing [[docs](services/py-fetcher/README.md)] |
| db               | PostgreSQL + pgvector  | 5432 | Data persistence and vector search        |

➡️ **Traefik Dashboard**: [http://localhost:8080/dashboard/](http://localhost:8080/dashboard/)

## 📚 Service Docs

| Service | Detailed README |
|---------|-----------------|
| Web Client | [web-client/README](web-client/README.md) |
| Spring API Server | [services/spring-api/README](services/spring-api/README.md) |
| GenAI Service | [services/py-genai/README](services/py-genai/README.md) |
| Topic Discovery Service | [services/py-topics/README](services/py-topics/README.md) |
| Article Fetcher Service | [services/py-fetcher/README](services/py-fetcher/README.md) |

## API Documentation

The complete REST API specification is available in `api/openapi.yaml` and published automatically via GitHub Pages:

| Format | Live link |
| ------ | --------- |
| ReDoc  | https://AET-DevOps25.github.io/team-dev_ops/api.html |
| Swagger UI | https://AET-DevOps25.github.io/team-dev_ops/swagger/ |

The `docs` GitHub Pages site is built by the workflow in `.github/workflows/docs.yml` every time `api/openapi.yaml` changes (or when you trigger the workflow manually).  

### View locally

```bash
# Install once
npm i -g redoc-cli swagger-ui-dist http-server

# Generate docs
redoc-cli bundle api/openapi.yaml -o docs/api.html

# Serve locally at http://localhost:8088
http-server docs -p 8088
```

# Architecture

> **TODO:** Embed the updated micro-service architecture diagram here (`docs/assets/Architecture.svg`).

> **TODO:** Add class diagram (`docs/assets/Class_Diagram.svg`).

> **TODO:** Add high-level use-case diagram (`docs/assets/use-case.svg`).

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
    type VARCHAR(50) NOT NULL,   -- 'Research' or 'Community'
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    feed_url TEXT NOT NULL,
    total_articles_processed INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT now()
)

-- Discovered topics (one row per semantic cluster)
topic (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analysis(id) ON DELETE CASCADE,
    query VARCHAR(255),
    type VARCHAR(50),
    feed_url TEXT,
    title TEXT NOT NULL,
    description TEXT,
    article_count INT DEFAULT 0,
    relevance INT DEFAULT 0,
    embedding vector(768),  -- Google Gemini embeddings
    created_at TIMESTAMP DEFAULT now()
)

-- Individual articles (deduplicated by external_id)
article (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analysis(id) ON DELETE CASCADE,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    snippet TEXT,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (analysis_id, external_id)  -- no duplicate arXiv IDs per analysis
)

-- Many-to-many link between topics ↔ articles
topic_article (
    topic_id   UUID REFERENCES topic(id) ON DELETE CASCADE,
    article_id UUID REFERENCES article(id) ON DELETE CASCADE,
    PRIMARY KEY (topic_id, article_id)
)
```

# Microservice Description
### Topic Discovery Service (`py-topics`)

The **py-topics** micro-service is responsible for clustering fetched articles into coherent semantic topics.
It receives a list of article embeddings from the GenAI service, uses **BERTopic** + **HDBSCAN** to detect
clusters, then labels each cluster with the help of an LLM (Google Gemini/OpenRouter).  The service exposes a
single REST endpoint `/api/v1/topics/discover` (see OpenAPI spec) that takes the original query, cached
embedding IDs and/or raw article metadata and returns a ranked list of topics with representative articles.

Key features:

* Adaptive topic count – specify `nr_topics` or let the model decide automatically.
* Minimum cluster size control (`min_cluster_size`).
* Stateless – all heavy lifting is done in-memory; results are sent back to the orchestrator which
  stores them in PostgreSQL.
* Fully covered by unit, integration and Pact provider tests (see `services/py-topics/tests`).

---


