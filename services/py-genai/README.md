# NicheExplorer GenAI Service

The GenAI service is the AI-powered engine of NicheExplorer, focused on data acquisition and embedding generation. It fetches research papers from ArXiv, classifies user queries, and generates high-quality semantic embeddings using Google Gemini AI. Embeddings are cached in ChromaDB for efficient retrieval by the Topic Discovery service.

---

## 1 · Responsibilities in one glance
* **Query classification** – determines appropriate ArXiv categories from natural language queries
* **ArXiv integration** – fetches research papers by category using the official ArXiv API
* **Embedding generation** – creates semantic embeddings using Google Gemini AI API
* **ChromaDB caching** – stores and retrieves embeddings efficiently with batch processing
* **REST endpoints** – exposes `/classify`, `/arxiv/search`, `/embed`, and `/embed-batch` for the microservices architecture

```
Query → Classification → ArXiv Fetch → Embedding Generation → ChromaDB Cache → Topic Discovery Service
```

### **Service Structure**
```
src/
├── main.py                 # FastAPI application entry point
├── routers/                # API endpoint handlers
│   ├── arxiv.py           # ArXiv search and category endpoints
│   ├── classification.py   # Query classification
│   └── embedding.py       # Vector embedding operations
├── services/               # Core AI services
│   ├── arxiv_service.py           # ArXiv API integration
│   ├── embedding_service.py      # Google Gemini embeddings + ChromaDB
│   ├── google_client.py          # Google Gemini API client
│   └── openweb_client.py         # Open WebUI API integration
├── models/                 # Data models and schemas
│   └── schemas.py         # Pydantic models for API
└── config/                 # Configuration management
    └── settings.py        # Environment and model settings
```

## 🔄 Microservices Integration

> Note – This service focuses on data acquisition and embedding generation. Topic discovery and clustering are handled by the dedicated Topic Discovery service.

---

## 3 · Processing pipeline (REST architecture)
1. **Classification** – Analyze natural language queries to determine appropriate ArXiv categories (cs.CV, cs.AI, etc.)
2. **ArXiv Search** – Fetch research papers by category using advanced ArXiv API queries
3. **Batch Embedding** – Generate semantic embeddings for multiple papers efficiently using Google Gemini
4. **ChromaDB Caching** – Store embeddings with paper IDs for fast retrieval and reuse
5. **API Response** – Return structured data to Java API server or Topic Discovery service
6. **Embedding Retrieval** – Serve cached embeddings to Topic Discovery service for clustering

---

## 4 · Configuration & environment
* `GOOGLE_API_KEY` – optional; unlocks Gemini embeddings.  If missing the service silently switches to the local Sentence-Transformer model.
* `CHAIR_API_KEY` - necessary to use the models hosted by the chair. Currently this is only utilized for the /classify endpoint.
* Processing limits such as `MAX_ARTICLES_PER_REQUEST` and `MIN_TREND_FREQUENCY` are centralised in `config/settings.py` and can be tuned without code changes.

---

## 5 · Public endpoints (no payloads shown)
1. **POST `/classify`** – determines if query is "research" or "community" and suggests appropriate ArXiv category
2. **POST `/arxiv/search`** – fetches research papers by ArXiv category or advanced query
3. **POST `/embed`** – generates single embedding for text using Google Gemini
4. **POST `/embed-batch`** – efficient batch embedding generation with ChromaDB caching
5. **POST `/embeddings-by-ids`** – retrieves cached embeddings by paper IDs for Topic Discovery service

---

This document intentionally omits implementation code so it can be pasted anywhere without syntax-highlighting noise while still giving developers a clear picture of how the GenAI layer feeds the rest of NicheExplorer.
