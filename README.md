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
                               │ JDBC            │   │ ArXiv API
                               ▼                 │   │ Google AI
                        ┌──────────────┐        │   │
                        │ PostgreSQL + │        │   │
                        │  pgvector    │        │   │
                        └──────────────┘        │   │
                               ▲                │   │
                               │ ChromaDB       │   │
                               │ Cache          │   │
                               └────────────────┘   │
                                                    │
                               ┌─────────────┐     │
                               │ Topic       │ ◀───┘
                               │ Discovery   │
                               │ (port 8100) │
                               └─────────────┘
```

Component roles:
* **Frontend** – React + Vite SPA (client container)
* **API Server** – Spring Boot service that orchestrates the pipeline and persists data
* **GenAI Service** – FastAPI service using ArXiv API and Google Gemini for embeddings with ChromaDB caching
* **Topic Discovery** – Lightweight FastAPI service for HDBSCAN clustering and topic labeling
* **Database** – PostgreSQL 15 with `pgvector` extension for semantic search

---

## Processing Pipeline

1. **Query submission** – User enters a question like "current trends in computer vision" or builds advanced queries
2. **Query classification** – GenAI service determines appropriate ArXiv category (e.g., cs.CV for computer vision)
3. **Article harvesting** – GenAI service fetches recent papers by category via ArXiv API (up to *N* entries, default 50)
4. **Embedding generation** – Google Gemini API generates semantic embeddings for each paper, cached in ChromaDB
5. **Topic discovery** – Topic Discovery service uses HDBSCAN clustering on cached embeddings to find meaningful subtopics
6. **Topic labeling** – Advanced NLP techniques extract meaningful titles and descriptions for each topic cluster
7. **Storage** – Topics, articles and their embeddings are stored with full metadata
8. **Presentation** – Frontend displays ranked topics with query details and expandable articles

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

The system uses an advanced microservices approach with proper separation of concerns:

1. **Data Acquisition** – GenAI service fetches articles via ArXiv API using category-based queries
2. **Embedding Generation** – Google Gemini API creates semantic embeddings, cached in ChromaDB for efficiency
3. **Semantic Clustering** – Topic Discovery service uses HDBSCAN algorithm on cached embeddings for optimal cluster detection
4. **Topic Labeling** – Multi-strategy NLP approach extracts meaningful titles:
   * Title phrase extraction from paper titles
   * Technical term detection from abstracts
   * TF-IDF analysis on n-grams for keyword relevance
5. **Topic Generation** – Each cluster becomes a topic with:
   * Title → Meaningful research area (e.g., "Neural Networks", "Object Detection")
   * Description → Context-aware description of the research focus
   * Relevance score → Clustering confidence (0-100)
6. **Ranking** – Topics sorted by relevance and article count

**AI Enhancement**: Google Gemini embeddings enable precise semantic understanding and clustering of research papers.

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

### **Complete API Reference**

#### **Java API Server (port 8080)**
- `POST /analyze` - **Main analysis endpoint**: Orchestrates the entire pipeline from query to topics
- `GET /analysis/history` - **Analysis history**: Retrieve past analyses with pagination and filtering
- `DELETE /analysis/{id}` - **Delete analysis**: Remove analysis and all associated data

#### **GenAI Service (port 8000)**
- `POST /classify` - **Query classification**: Determines if query is research/community and suggests ArXiv category
- `POST /arxiv/search` - **Paper fetching**: Retrieves research papers by ArXiv category or advanced query
- `POST /embed` - **Single embedding**: Generates semantic embedding for one text using Google Gemini
- `POST /embed-batch` - **Batch embeddings**: Efficiently generates embeddings for multiple papers with ChromaDB caching
- `POST /embeddings-by-ids` - **Cached retrieval**: Retrieves stored embeddings by paper IDs for Topic Discovery service
- `GET /arxiv/categories` - **Available categories**: Lists ArXiv research categories organized by field
- `POST /arxiv/build-query` - **Advanced queries**: Constructs complex ArXiv search syntax from terms and categories

#### **Topic Discovery Service (port 8100)**
- `POST /discover-topics-from-embeddings` - **Main clustering endpoint**: Uses cached embeddings to discover semantic topics via HDBSCAN

#### **Why Each Endpoint is Needed:**

**Query Processing Flow:**
1. `/classify` - Converts natural language to appropriate data source and category
2. `/arxiv/search` - Fetches relevant research papers by category for focused analysis
3. `/embed-batch` - Generates semantic understanding of papers using AI, cached for efficiency

**Topic Discovery Flow:**
4. `/embeddings-by-ids` - Retrieves cached embeddings without regenerating them
5. `/discover-topics-from-embeddings` - Clusters papers into meaningful research subtopics
6. `/analyze` - Orchestrates the entire pipeline and persists results

**User Experience:**
- `/analysis/history` - Allows users to revisit past analyses and build on previous research
- `/arxiv/categories` & `/arxiv/build-query` - Enables advanced users to construct precise research queries

This architecture ensures **separation of concerns**, **caching efficiency**, and **specialized optimization** for each step of the analysis pipeline.

### **Performance Optimizations**
- **Ultra-lightweight containers**: Fast builds using `uv` package manager
- **Google AI integration**: No local model downloads required
- **Efficient ArXiv API**: Direct access to latest research papers by category
- **Smart caching**: Embeddings cached in ChromaDB with batch processing
- **Microservices architecture**: Specialized services for optimal performance

---

## Architecture Benefits

1. **Reliability**: ArXiv API much more stable than RSS feeds
2. **Advanced Search**: Support for complex research queries with category filtering
3. **AI-Powered**: Google Gemini provides state-of-the-art semantic embeddings
4. **Scalable**: Microservices architecture with specialized responsibilities
5. **Efficient**: ChromaDB caching reduces redundant API calls and speeds up clustering
6. **Extensible**: Clean separation between embedding generation and topic discovery

---

