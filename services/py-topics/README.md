# NicheExplorer Topic Discovery Service

The Topic Discovery service is a specialized microservice focused on semantic clustering and topic labeling. It uses advanced machine learning algorithms (HDBSCAN) to discover meaningful research topics from cached embeddings and generates human-readable topic descriptions.

---

## 1 · Responsibilities in one glance
* **Semantic clustering** – uses HDBSCAN algorithm on cached embeddings to find optimal topic clusters
* **Topic labeling** – multi-strategy NLP approach to generate meaningful topic titles and descriptions
* **Batch processing** – efficiently processes embeddings retrieved from GenAI service's ChromaDB cache
* **REST endpoints** – exposes `/discover-topics-from-embeddings` for the proper microservices architecture

```
Cached Embeddings → HDBSCAN Clustering → Topic Labeling → Meaningful Research Topics
```

### **Service Structure**
```
src/
├── main.py                 # FastAPI application entry point
├── services/               # Core clustering services
│   └── topic_service.py   # HDBSCAN clustering and topic labeling
├── models.py              # Pydantic models for API requests/responses
└── requirements.txt       # Python dependencies (scikit-learn, HDBSCAN, etc.)
```

## 🔄 Advanced Clustering Pipeline

> Note – This service assumes embeddings are already generated and cached by the GenAI service. It focuses purely on clustering and topic discovery.

---

## 3 · Clustering algorithm (technical details)
1. **Embedding Retrieval** – fetches cached embeddings from GenAI service by paper IDs
2. **Dimensionality Reduction** – uses UMAP to reduce embeddings for optimal clustering
3. **Adaptive Clustering** – HDBSCAN with dynamic parameters based on dataset size
4. **Topic Labeling** – multi-strategy approach:
   * Title phrase extraction from paper titles
   * Technical term detection using regex patterns
   * TF-IDF analysis on meaningful n-grams
5. **Quality Filtering** – removes noise and generic terms to ensure meaningful topics
6. **Ranking** – sorts topics by clustering confidence and article count

---

## 4 · Configuration & performance
* **Lightweight container** – uses `uv` package manager for fast builds
* **No AI dependencies** – pure ML algorithms (scikit-learn, HDBSCAN, UMAP)
* **Adaptive parameters** – clustering parameters adjust based on dataset size
* **Efficient processing** – optimized for cached embeddings and batch operations

---

## 5 · Public endpoints
1. **POST `/discover-topics-from-embeddings`** – main endpoint: takes paper metadata and IDs, returns semantic topics

---

## 6 · Topic quality features
* **Meaningful titles** – extracts research areas like "Neural Networks", "Object Detection", "Image Segmentation"
* **Context-aware descriptions** – generates descriptive text explaining the research focus
* **Technical accuracy** – uses domain-specific patterns to identify computer science terminology
* **Relevance scoring** – clustering confidence provides meaningful relevance scores (0-100)

This service ensures that topics are semantically meaningful and represent distinct research areas rather than generic keyword buckets.
