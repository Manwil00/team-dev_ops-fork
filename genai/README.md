# NicheExplorer GenAI Service

The GenAI service is the AI/ML brain of NicheExplorer, built with Python and FastAPI. It performs sophisticated semantic analysis, trend extraction, and vector embedding generation using advanced natural language processing techniques and machine learning models.

## 🧠 AI/ML Architecture Overview

The GenAI service implements a multi-stage ML pipeline for trend discovery:

```
RSS Articles → Preprocessing → Semantic Analysis → Topic Clustering → Trend Ranking → Vector Embeddings
```

### **Service Structure**
```
src/
├── main.py                 # FastAPI application entry point
├── routers/                # API endpoint handlers
│   ├── trends.py          # Trend extraction endpoints
│   ├── classification.py   # Query classification
│   └── embedding.py       # Vector embedding operations
├── services/               # Core ML services
│   ├── langchain_trends_service.py  # Main trend analysis engine
│   ├── google_client.py            # Google Gemini API integration
│   └── embedding_service.py        # Vector embedding service
├── models/                 # Data models and schemas
│   └── schemas.py         # Pydantic models for API
├── config/                 # Configuration management
│   └── settings.py        # Environment and model settings
└── download_model.py      # Pre-download ML models
```

## 🔄 Complete ML Pipeline

### 1. **Article Preprocessing & Normalization**

```python
def preprocess_articles(self, articles: List[Dict]) -> List[Dict]:
    """Clean and normalize article content for analysis"""
    processed = []
    for article in articles:
        # Text cleaning and normalization
        clean_title = self._clean_text(article.get('title', ''))
        clean_content = self._clean_text(article.get('summary', ''))
        
        # Skip articles with insufficient content
        if len(clean_title.split()) < 3:
            continue
            
        processed.append({
            'title': clean_title,
            'content': clean_content,
            'link': article.get('link', ''),
            'summary': clean_content[:500]  # Truncate for processing
        })
    
    return processed
```

### 2. **Semantic Topic Clustering**

The service uses keyword-based semantic grouping with predefined ML/AI vocabulary:

```python
ML_KEYWORDS = {
    'neural': ['neural', 'neuron', 'network', 'cnn', 'rnn', 'lstm', 'gru'],
    'deep': ['deep', 'deeplearning', 'dnn'],
    'learning': ['learning', 'machine learning', 'ml', 'training'],
    'vision': ['vision', 'computer vision', 'cv', 'image', 'visual'],
    'language': ['language', 'nlp', 'text', 'linguistic', 'bert', 'gpt'],
    'model': ['model', 'algorithm', 'architecture'],
    'data': ['data', 'dataset', 'big data', 'analytics'],
    'ai': ['artificial intelligence', 'ai', 'intelligent']
}

def _simple_keyword_grouping(self, articles: List[Dict]) -> List[Dict]:
    """Group articles by semantic keyword matching"""
    keyword_groups = {}
    
    for article in articles:
        text = f"{article['title']} {article['content']}".lower()
        
        # Find matching keywords
        for category, keywords in self.ML_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    if category not in keyword_groups:
                        keyword_groups[category] = []
                    keyword_groups[category].append(article)
                    break
    
    # Convert groups to topics with metadata
    topics = []
    for category, group_articles in keyword_groups.items():
        if len(group_articles) >= 2:  # Minimum threshold
            topic = self._create_topic_from_group(category, group_articles)
            topics.append(topic)
    
    return sorted(topics, key=lambda x: x['article_count'], reverse=True)
```

### 3. **Relevance Scoring Algorithm**

```python
def _calculate_relevance_score(self, articles: List[Dict], keywords: List[str]) -> int:
    """Calculate relevance score based on keyword frequency and article quality"""
    if not articles:
        return 0
    
    total_score = 0
    for article in articles:
        text = f"{article['title']} {article['content']}".lower()
        
        # Keyword frequency scoring
        keyword_count = sum(text.count(kw.lower()) for kw in keywords)
        
        # Title presence bonus (titles are more important)
        title_bonus = sum(5 for kw in keywords if kw.lower() in article['title'].lower())
        
        # Content length normalization
        content_quality = min(len(article['content'].split()) / 20, 3)
        
        article_score = (keyword_count * 2) + title_bonus + content_quality
        total_score += article_score
    
    # Normalize to 0-100 scale
    max_possible_score = len(articles) * 15  # Theoretical maximum
    normalized_score = min(int((total_score / max_possible_score) * 100), 100)
    
    return max(normalized_score, 30)  # Minimum score for discovered trends
```

### 4. **Vector Embedding Generation**

The service generates high-dimensional vector embeddings for semantic similarity:

```python
class EmbeddingService:
    def __init__(self):
        # Initialize Google Gemini embeddings
        self.embeddings_client = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate 768-dimensional embedding vector"""
        try:
            # Clean and prepare text
            clean_text = self._prepare_text_for_embedding(text)
            
            # Generate embedding using Google's model
            embedding = await self.embeddings_client.aembed_query(clean_text)
            
            # Normalize vector for cosine similarity
            normalized = self._normalize_vector(embedding)
            
            return normalized
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [0.0] * 768  # Return zero vector on failure
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize vector to unit length for cosine similarity"""
        import math
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            return [x / magnitude for x in vector]
        return vector
```

## 🚀 API Endpoints

### **Trend Extraction Endpoint**

```python
@router.post("/extract-trends", response_model=TrendsResponse)
async def extract_trends(req: TrendsRequest):
    """Extract trending topics from RSS feed using semantic clustering"""
    try:
        logger.info(f"Extracting trends for query: {req.query}")
        
        # Use LangChain-based service for semantic understanding
        topics = langchain_trends_service.extract_trending_topics(
            feed_url=req.feed_url,
            max_articles=req.max_articles,
            min_frequency=req.min_frequency
        )
        
        return TrendsResponse(
            query=req.query,
            feed_url=req.feed_url,
            trends=topics,
            total_articles_processed=len(topics) * 5  # Estimate
        )
    
    except Exception as e:
        logger.error(f"Error extracting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### **Query Classification Endpoint**

```python
@router.post("/classify", response_model=ClassificationResponse)
async def classify_query(request: ClassificationRequest):
    """Classify query as research or community-focused"""
    try:
        classification = google_client.classify_query(request.query)
        
        return ClassificationResponse(
            query=request.query,
            source=classification['source'],
            confidence=classification['confidence'],
            feed=classification['suggested_feed']
        )
    
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### **Vector Embedding Endpoint**

```python
@router.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """Generate vector embedding for text content"""
    try:
        embedding = await embedding_service.generate_embedding(request.text)
        
        return EmbeddingResponse(
            text=request.text,
            embedding=embedding,
            dimensions=len(embedding),
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## 🤖 Machine Learning Models

### **Pre-trained Models Used**

1. **Google Gemini Embeddings (`models/embedding-001`)**
   - 768-dimensional dense vectors
   - Trained on diverse text corpora
   - Optimized for semantic similarity tasks

2. **Sentence Transformers (Fallback)**
   - `all-MiniLM-L6-v2` for lightweight embeddings
   - 384-dimensional vectors
   - Local processing capability

### **Model Management**

```python
# download_model.py - Pre-download models for offline use
import sentence_transformers

def download_models():
    """Download and cache ML models for offline use"""
    try:
        # Download sentence transformer model
        model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
        model.save('./models/sentence-transformer')
        
        print("Models downloaded successfully")
    except Exception as e:
        print(f"Model download failed: {e}")

if __name__ == "__main__":
    download_models()
```

## 📊 Data Processing Pipeline

### **RSS Feed Processing**

```python
def fetch_and_process_feed(self, feed_url: str, max_articles: int) -> List[Dict]:
    """Fetch articles from RSS feed and preprocess for analysis"""
    try:
        import feedparser
        
        # Fetch RSS feed
        feed = feedparser.parse(feed_url)
        logger.info(f"Fetched {len(feed.entries)} entries from {feed_url}")
        
        # Process entries
        articles = []
        for entry in feed.entries[:max_articles]:
            article = {
                'title': getattr(entry, 'title', ''),
                'content': getattr(entry, 'summary', ''),
                'link': getattr(entry, 'link', ''),
                'published': getattr(entry, 'published', ''),
                'authors': getattr(entry, 'authors', [])
            }
            
            # Validate and clean article
            if self._is_valid_article(article):
                cleaned_article = self._clean_article(article)
                articles.append(cleaned_article)
        
        return articles
        
    except Exception as e:
        logger.error(f"RSS processing failed: {e}")
        return []
```

### **Content Quality Assessment**

```python
def _is_valid_article(self, article: Dict) -> bool:
    """Assess article quality for inclusion in analysis"""
    
    # Check minimum content requirements
    if not article.get('title') or len(article['title']) < 10:
        return False
    
    if not article.get('content') or len(article['content']) < 50:
        return False
    
    # Filter out common spam patterns
    spam_indicators = ['click here', 'buy now', 'limited time']
    content_lower = article['content'].lower()
    
    if any(indicator in content_lower for indicator in spam_indicators):
        return False
    
    # Check for sufficient academic/technical content
    technical_terms = ['algorithm', 'method', 'analysis', 'research', 'study']
    has_technical_content = any(term in content_lower for term in technical_terms)
    
    return has_technical_content
```

## 🔧 Configuration & Environment

### **Environment Variables**

```python
# config/settings.py
import os
from typing import Optional

class Settings:
    # Google API Configuration
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Model Configuration
    EMBEDDING_MODEL: str = "models/embedding-001"
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    
    # Processing Limits
    MAX_ARTICLES_PER_REQUEST: int = 100
    MIN_TREND_FREQUENCY: int = 2
    MAX_TRENDS_RETURNED: int = 10
    
    # Text Processing
    MAX_TEXT_LENGTH: int = 8000
    MIN_TITLE_LENGTH: int = 10
    MIN_CONTENT_LENGTH: int = 50
    
    # Cache Configuration
    ENABLE_CACHING: bool = True
    CACHE_TTL_SECONDS: int = 3600

settings = Settings()
```

### **Dependencies & Requirements**

```txt
# Core Framework
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.4.2

# ML & NLP Libraries
langchain==0.0.335
langchain-google-genai==0.0.6
sentence-transformers==2.2.2
scikit-learn==1.3.2
numpy==1.24.3

# Text Processing
feedparser==6.0.10
beautifulsoup4==4.12.2
python-multipart==0.0.6

# Environment & Utilities
python-dotenv==1.0.0
requests==2.31.0
aiofiles==23.2.1
```

## 🧪 Testing & Validation

### **Unit Testing**

```python
import pytest
from unittest.mock import Mock, patch
from services.langchain_trends_service import LangChainTrendsService

class TestTrendsService:
    
    @pytest.fixture
    def trends_service(self):
        return LangChainTrendsService()
    
    def test_keyword_grouping(self, trends_service):
        # Test semantic keyword grouping
        articles = [
            {'title': 'Deep Neural Networks', 'content': 'CNN architecture'},
            {'title': 'Machine Learning', 'content': 'supervised learning'}
        ]
        
        topics = trends_service._simple_keyword_grouping(articles)
        
        assert len(topics) > 0
        assert any(topic['title'] == 'Neural Research' for topic in topics)
    
    def test_relevance_scoring(self, trends_service):
        # Test relevance score calculation
        articles = [{'title': 'Neural Networks', 'content': 'deep learning'}]
        keywords = ['neural', 'deep', 'learning']
        
        score = trends_service._calculate_relevance_score(articles, keywords)
        
        assert 0 <= score <= 100
        assert score > 30  # Should exceed minimum threshold
```

### **Integration Testing**

```python
@pytest.mark.asyncio
async def test_extract_trends_endpoint():
    """Test complete trend extraction pipeline"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    request_data = {
        "query": "machine learning",
        "feed_url": "https://rss.arxiv.org/rss/cs.CV",
        "max_articles": 20,
        "min_frequency": 2
    }
    
    response = client.post("/extract-trends", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert len(data["trends"]) > 0
```

## 🚀 Deployment & Performance

### **Docker Configuration**

```dockerfile
FROM python:3.11-slim

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y \
    gcc g++ libblas-dev liblapack-dev libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY config/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --only-binary=all -r requirements.txt

# Copy application code
COPY src/ ./src/

# Pre-download ML models
RUN mkdir -p /app/models && chmod 755 /app/models
RUN python3 src/download_model.py || echo "Model download failed, will download on first use"

# Run application
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Performance Optimizations**

```python
# Async processing for better throughput
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-load models
    await preload_models()
    yield
    # Shutdown: Cleanup resources
    await cleanup_resources()

app = FastAPI(lifespan=lifespan)

# Memory-efficient batch processing
async def process_articles_in_batches(articles: List[Dict], batch_size: int = 10):
    """Process articles in batches to manage memory usage"""
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        yield await process_batch(batch)
```

### **Monitoring & Logging**

```python
import logging
import time
from functools import wraps

# Performance monitoring decorator
def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/genai.log')
    ]
)
```

## 🔮 Future Enhancements

### **Advanced ML Features**
- **Dynamic Clustering**: Implement DBSCAN/KMeans for automatic cluster discovery
- **Topic Modeling**: Use LDA or BERT-based topic modeling for better trend detection
- **Sentiment Analysis**: Add sentiment scoring for trend emotional analysis
- **Cross-domain Transfer**: Apply learned patterns across different domains

### **Performance Improvements**
- **Model Caching**: Cache embeddings and classification results
- **Distributed Processing**: Scale with Celery for heavy workloads
- **Streaming Processing**: Real-time trend detection with Apache Kafka
- **GPU Acceleration**: Leverage CUDA for faster model inference

---

The NicheExplorer GenAI service provides sophisticated AI/ML capabilities for semantic trend analysis, combining modern NLP techniques with efficient processing pipelines to deliver actionable insights from research literature and community discussions. 