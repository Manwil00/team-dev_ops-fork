# NicheExplorer

NicheExplorer is a micro-services platform that monitors research articles from ArXiv and community discussions from Reddit, groups related content into topics using AI-powered analysis, and serves insights through an intuitive web interface.

## Architecture

```
React Client (80) → Spring Boot API (8080) → GenAI Service (8000)
                                          ↓
                 PostgreSQL + pgvector ← Topic Discovery (8100)
                                     ↑
                               Article Fetcher (8200)
```

**Services:**
- **spring-api**: Main API server, orchestrates pipeline, persists data
- **py-genai**: AI service using Google Gemini for embeddings, ChromaDB caching
- **py-topics**: HDBSCAN clustering for topic discovery
- **py-fetcher**: Article retrieval from ArXiv API and Reddit RSS
- **web-client**: React frontend with TypeScript
- **Database**: PostgreSQL 15 with pgvector extension

## Quick Start

**Prerequisites:** Docker Desktop

**Local Development:**
```bash
git clone <repository> && cd team-dev_ops
echo "GOOGLE_API_KEY=<key>\nCHAIR_API_KEY=<key>" > .env
docker-compose -f infra/docker-compose.yml up -d --build
```

**Access:** http://localhost (frontend), http://localhost:8080/swagger-ui.html (API docs)

## Project Structure

```
team-dev_ops/
├── api/                    # OpenAPI specification & code generation
│   ├── openapi.yaml       # Single source of truth API contract
│   └── scripts/gen-all.sh # Generate clients & server stubs
├── services/              # Microservices implementation
│   ├── spring-api/        # Java Spring Boot API server
│   ├── py-genai/         # Python FastAPI AI service
│   ├── py-topics/        # Python FastAPI topic discovery
│   ├── py-fetcher/       # Python FastAPI article fetcher
│   └── web-client/       # React TypeScript frontend
├── infra/                 # Infrastructure as Code
│   ├── docker-compose.yml # Local development
│   ├── compose.aws.yml   # AWS deployment
│   ├── helm/             # Kubernetes charts
│   ├── terraform/        # Cloud infrastructure
│   ├── ansible/          # Configuration management
│   └── scripts/          # Infrastructure automation
└── .github/workflows/    # CI/CD pipeline
```

## Development Workflow

**API-First Development:**
```bash
# 1. Update OpenAPI spec
vim api/openapi.yaml
# 2. Generate code
./api/scripts/gen-all.sh
# 3. Implement generated interfaces
```

**Local Service Development:**
```bash
# Python services
cd services/py-genai && pip install -r requirements.txt && uvicorn src.main:app --reload
# Frontend
cd services/web-client && npm install && npm run dev
# Java API
cd services/spring-api && ./gradlew bootRun
```

## API Endpoints

**Main API Server (8080):**
- `POST /api/analyze` - Complete analysis pipeline
- `GET /api/analysis/history` - Analysis history with pagination
- `DELETE /api/analysis/{id}` - Delete analysis

**GenAI Service (8000):**
- `POST /classify` - Query classification and ArXiv category detection
- `POST /embed-batch` - Batch embedding generation with caching
- `GET /arxiv/categories` - Available research categories

**Article Fetcher (8200):**
- `POST /fetch` - Retrieve articles from ArXiv or Reddit

**Topic Discovery (8100):**
- `POST /discover-topic` - HDBSCAN clustering and topic labeling

## Database Schema

```sql
CREATE TABLE analysis (
    id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    type VARCHAR(50) NOT NULL,
    feed_url TEXT,
    total_articles_processed INTEGER DEFAULT 0
);

CREATE TABLE topic (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analysis(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    relevance INTEGER CHECK (relevance BETWEEN 0 AND 100),
    article_count INTEGER DEFAULT 0,
    embedding VECTOR(768)
);

CREATE TABLE article (
    id UUID PRIMARY KEY,
    topic_id UUID REFERENCES topic(id),
    title TEXT NOT NULL,
    link TEXT UNIQUE,
    snippet TEXT,
    content_hash VARCHAR(64) UNIQUE,
    embedding VECTOR(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Deployment

**AWS (ECS/Fargate):**
```bash
cd infra
docker-compose -f compose.aws.yml up -d
```

**Kubernetes:**
```bash
cd infra/helm
helm install niche-explorer ./niche-explorer/
```

**Cloud Infrastructure:**
```bash
cd infra/terraform && terraform init && terraform apply
```

## Configuration

**Environment Variables:**
- `GOOGLE_API_KEY` - Required for AI embeddings
- `CHAIR_API_KEY` - Required for query classification
- `DATABASE_URL` - PostgreSQL connection string
- `CHROMA_HOST` - ChromaDB host for embedding cache

**Database Initialization:**
```bash
cd infra/scripts
./setup-database.ps1 -Action init
```

## DevOps Features

- **API-First Design**: OpenAPI 3.0 with automatic code generation
- **CI/CD Pipeline**: Automated testing and building for all services
- **Pre-commit Hooks**: OpenAPI validation and formatting
- **Container Strategy**: Multi-stage Docker builds with optimization
- **Infrastructure as Code**: Docker Compose, Kubernetes, Terraform support
- **Monitoring**: Health checks and logging for all services

## Processing Pipeline

1. User submits research query
2. GenAI service classifies query and determines ArXiv category
3. Article Fetcher retrieves papers from ArXiv API or Reddit RSS
4. Google Gemini generates semantic embeddings (cached in ChromaDB)
5. Topic Discovery clusters embeddings using HDBSCAN algorithm
6. System extracts meaningful topic labels and descriptions
7. Results stored in PostgreSQL with vector indexes
8. Frontend displays ranked topics with expandable articles

**Example Query:** "current trends in computer vision" → cs.CV category → ArXiv papers → embeddings → topic clusters → "Object Detection", "Neural Networks", etc.

## Technical Stack

- **Backend**: Java 21 (Spring Boot), Python 3.11 (FastAPI)
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Database**: PostgreSQL 15 with pgvector extension
- **AI/ML**: Google Gemini API, ChromaDB, HDBSCAN clustering
- **Infrastructure**: Docker, Kubernetes, Terraform, Ansible
- **API**: OpenAPI 3.0 specification with code generation 