# NicheExplorer

NicheExplorer is a micro-services platform that monitors research articles from ArXiv and community discussions from Reddit, groups related content into topics using AI-powered analysis, and serves insights through an intuitive web interface.

---

## Architecture Overview

```
┌──────────────┐  HTTP  ┌──────────────┐  REST  ┌─────────────┐
│ React Client │ ─────▶ │ Spring Boot  │ ─────▶ │  GenAI      │
│  (port 80)   │        │  API Server  │        │  Service    │
└──────────────┘        │ (port 8080)  │        │ (port 8000) │
                        └──────┬──────┘        └────┬──────┘
                               │ JDBC                  │ ArXiv API
                               ▼                      │ Google AI
                        ┌──────────────┐             │
                        │ PostgreSQL + │◀────────────┘
                        │  pgvector    │
                        └──────────────┘
```

Component roles:
* **Frontend** – React + Vite SPA (client container)
* **API Server** – Spring Boot service that orchestrates the pipeline and persists data
* **GenAI Service** – FastAPI service using ArXiv API and Google Gemini for AI-powered analysis
* **Database** – PostgreSQL 15 with `pgvector` extension for semantic search

---

## Processing Pipeline

1. **Query submission** – User enters a question like "current trends in computer vision" or builds advanced queries
2. **Query processing** – System converts natural language to ArXiv API queries or uses advanced search syntax
3. **Article harvesting** – GenAI service fetches recent papers via ArXiv API (up to *N* entries, default 50)
4. **AI-powered analysis** – Google Gemini API processes articles for semantic understanding
5. **Topic discovery** – Articles are grouped into meaningful topics using keyword clustering
6. **Storage** – Topics, articles and their embeddings are stored with full metadata
7. **Presentation** – Frontend displays ranked topics with query details and expandable articles

---

## Search Capabilities

### **Simple Category Search**
- Use ArXiv categories like `cs.CV`, `cs.AI`, `cs.LG`
- Example: "What are current trends in AI research?" → searches `cs.AI`

### **Advanced Query Search**
- Combine search terms with categories: `all:"graph neural network"+AND+cat:cs.CV`
- Support for ArXiv query operators: `ti:`, `au:`, `abs:`, `cat:`
- Boolean operators: `+AND+`, `+OR+`

### **Natural Language Processing**
- Auto-converts queries like "machine learning in computer vision"
- Maps to appropriate ArXiv categories and search terms
- Intelligent keyword extraction and category selection

---

## Topic Discovery Algorithm

The system uses a hybrid approach implemented in `genai/src/services/langchain_trends_service.py`:

1. **Data Acquisition** – Fetch articles via ArXiv API using optimized queries
2. **Keyword Analysis** – Extract meaningful terms from titles and abstracts
3. **Smart Grouping** – Articles are clustered by semantic similarity and common keywords
4. **Topic Generation** – Each cluster becomes a topic with:
   * Title → "<keyword> Research"
   * Description → "Recent research advances in <keyword>"
   * Relevance score → `50 + min(article_count × 3, 50)` (range 50-100)
5. **Ranking** – Topics sorted by relevance and article count; top 6 returned

**AI Enhancement**: Google Gemini API provides semantic embeddings for advanced clustering (when enabled).

---

## Database Schema

```sql
CREATE TABLE analysis (
    id          UUID PRIMARY KEY,
    query       TEXT      NOT NULL,
    timestamp   TIMESTAMPTZ DEFAULT NOW(),
    type        VARCHAR(50) NOT NULL,
    feed_url    TEXT,  -- Now stores ArXiv queries or Reddit URLs
    total_articles_processed INTEGER DEFAULT 0
);

CREATE TABLE trend (
    id              UUID PRIMARY KEY,
    analysis_id     UUID REFERENCES analysis(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    relevance_score INTEGER CHECK (relevance_score BETWEEN 0 AND 100),
    article_count   INTEGER DEFAULT 0,
    embedding       VECTOR(768)  -- Google Gemini embeddings
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
    published_date TIMESTAMPTZ,
    categories    TEXT[]  -- ArXiv categories
);

CREATE INDEX article_embedding_idx ON article USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX trend_embedding_idx ON trend USING ivfflat (embedding vector_cosine_ops);
```

---

## Quick Start

1. **Prerequisites**: Install Docker Desktop
2. **Clone**: `git clone <repository> && cd team-dev_ops`
3. **Environment**: Create `.env` with `GOOGLE_API_KEY=<your-key>` (required for AI features)
4. **Deploy**: `docker-compose up -d` – starts all services
5. **Access**: Open <http://localhost> and start exploring research trends

### **Example Queries to Try:**
- "What are current trends in AI research?"
- "Graph neural networks in computer vision" (advanced mode)
- "Transformer architectures for natural language processing"

---

## Advanced Features

### **Frontend Capabilities**
- **Auto-detect mode**: Automatically determines research vs community focus
- **Manual mode**: Choose between ArXiv research or Reddit community data
- **Advanced search**: Build complex ArXiv queries with search terms + categories
- **Query visualization**: See exactly what search was performed
- **Real-time preview**: Watch as advanced queries are constructed

### **API Endpoints**
- `POST /extract-trends` - Main analysis endpoint
- `GET /arxiv-categories` - Available ArXiv research categories
- `POST /build-advanced-query` - Construct advanced search queries
- `POST /classify` - Auto-classify queries for source determination

### **Performance Optimizations**
- **Ultra-lightweight containers**: ~5 minute build time (was 20+ minutes)
- **Google AI integration**: No local model downloads required
- **Efficient ArXiv API**: Direct access to latest research papers
- **Smart caching**: Embeddings and results cached in PostgreSQL

---

## Architecture Benefits

1. **Reliability**: ArXiv API much more stable than RSS feeds
2. **Advanced Search**: Support for complex research queries
3. **AI-Powered**: Google Gemini provides state-of-the-art language understanding
4. **Scalable**: Lightweight containers, efficient resource usage
5. **Extensible**: Easy to add new data sources and AI capabilities

---

## Roadmap

* ✅ **ArXiv API Integration** - Replace RSS with official ArXiv API
* ✅ **Advanced Search Queries** - Support complex search syntax
* ✅ **Google AI Integration** - Use Gemini for embeddings and analysis
* 🔄 **Enhanced Semantic Clustering** - Implement DBSCAN-based topic discovery
* 📋 **Real-time Monitoring** - Scheduled background analysis
* 🚀 **Production Deployment** - Kubernetes with Helm charts in `helm/`
* 📊 **Analytics Dashboard** - Research trend visualization and insights 