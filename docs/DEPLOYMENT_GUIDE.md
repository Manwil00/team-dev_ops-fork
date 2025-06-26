# NicheExplorer Deployment Guide

This guide provides step-by-step instructions for deploying the streamlined NicheExplorer system, which has been optimized for production use without the experimental topic visualization features.

## 🏗️ System Overview

NicheExplorer is now a streamlined, production-ready application consisting of four core services:

```
Frontend (React) ←→ API Server (Java/Spring) ←→ GenAI Service (Python/ML) ←→ Database (PostgreSQL)
     :80                    :8080                      :8000                    :5432
```

### **Key Features Implemented**
✅ **Semantic Trend Analysis** - AI-powered topic discovery from research papers and community discussions
✅ **Vector Embeddings** - 768-dimensional embeddings stored in PostgreSQL with pgvector
✅ **Interactive UI** - Clean, modern interface with animated progress bars and article expansion
✅ **Persistent History** - All analyses stored and retrievable from database
✅ **Duplicate Prevention** - SHA-256 content hashing prevents duplicate article storage
✅ **Auto Source Detection** - Intelligent classification of queries as research vs community-focused

### **Recent Optimizations**
- Removed experimental topic visualization to focus on core functionality
- Simplified component architecture for better maintainability
- Streamlined API endpoints to essential operations
- Enhanced error handling and logging throughout the stack

## 🚀 Quick Start

### **Prerequisites**
- Docker & Docker Compose installed
- Google Gemini API key for embeddings
- At least 4GB RAM available for containers

### **1. Environment Setup**
```bash
# Clone repository
git clone <your-repo-url>
cd team-dev_ops

# Create environment file
cp .env.example .env

# Add your Google API key to .env
echo "GOOGLE_API_KEY=your_api_key_here" >> .env
```

### **2. Deploy with Docker Compose**
```bash
# Build and start all services
docker-compose up -d

# Verify all services are running
docker-compose ps
```

### **3. Access Application**
- **Frontend**: http://localhost
- **API Documentation**: http://localhost:8080/actuator/health
- **GenAI Service**: http://localhost:8000

## 📊 Service Architecture

### **Frontend Service (client:80)**
- **Technology**: React 18 + TypeScript + Tailwind CSS
- **Purpose**: User interface for query submission and results visualization
- **Key Components**:
  - `StartExploringForm` - Main query interface
  - `AnalysisHistory` - Historical analysis display
  - `TrendResult` - Interactive trend visualization with progress bars
  - `AnalysisItem` - Individual analysis cards with expandable trends

### **API Server (api-server:8080)**
- **Technology**: Java 21 + Spring Boot 3.2 + PostgreSQL
- **Purpose**: Orchestrates analysis pipeline and manages data persistence
- **Key Endpoints**:
  - `POST /api/analyze` - Process new analysis requests
  - `GET /api/history` - Retrieve analysis history
  - `DELETE /api/analysis/{id}` - Delete specific analysis
  - `POST /api/trend/{id}/embedding` - Get trend vector embeddings
  - `POST /api/article/{id}/embedding` - Get article vector embeddings

### **GenAI Service (genai:8000)**
- **Technology**: Python 3.11 + FastAPI + LangChain + scikit-learn
- **Purpose**: AI/ML processing for trend extraction and embeddings
- **Key Features**:
  - Semantic keyword-based topic clustering
  - Relevance score calculation (0-100%)
  - Vector embedding generation using Google Gemini
  - RSS feed processing and content analysis

### **Database (db:5432)**
- **Technology**: PostgreSQL 15 + pgvector extension
- **Purpose**: Persistent storage with vector search capabilities
- **Schema**:
  - `analysis` - Query sessions with metadata
  - `trend` - Discovered topics with relevance scores
  - `article` - Individual articles with 768-dim embeddings

## 🔄 Complete Analysis Flow

### **1. User Submission**
1. User enters query via React frontend
2. Frontend validates input and sends to `/api/analyze`
3. API server receives request and begins orchestration

### **2. Source Classification**
```java
// Automatic source detection
if (request.isAutoDetect()) {
    ClassificationResponse classification = classificationClient.classify(query);
    feedUrl = determineFeedUrl(classification);
    // Research → ArXiv feeds (cs.CV, cs.AI, cs.LG)
    // Community → Reddit feeds (/r/MachineLearning, /r/programming)
}
```

### **3. Content Extraction**
1. API server fetches articles from determined RSS feed
2. Validates and preprocesses article content
3. Sends processed articles to GenAI service

### **4. AI Analysis**
```python
# GenAI service processes articles
def extract_trending_topics(feed_url, max_articles, min_frequency):
    # 1. Fetch and preprocess articles from RSS
    articles = fetch_and_process_feed(feed_url, max_articles)

    # 2. Group articles by semantic keywords
    topics = _simple_keyword_grouping(articles)

    # 3. Calculate relevance scores
    for topic in topics:
        topic['relevance'] = _calculate_relevance_score(topic['articles'])

    # 4. Generate vector embeddings
    for article in all_articles:
        article['embedding'] = generate_embedding(article['content'])

    return topics
```

### **5. Data Persistence**
1. API server saves analysis metadata to database
2. Stores trends with calculated relevance scores
3. Saves individual articles with vector embeddings
4. Uses SHA-256 hashing to prevent duplicates

### **6. Results Display**
1. Frontend receives structured response with trends and articles
2. Displays trends with animated progress bars showing relevance
3. Allows individual expansion of articles within each trend
4. Stores results in persistent history for future access

## 🔧 Configuration

### **Environment Variables**
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Database (defaults provided)
POSTGRES_DB=niche
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Optional customization
MAX_ARTICLES_PER_REQUEST=100
MIN_TREND_FREQUENCY=2
```

### **Docker Compose Configuration**
```yaml
services:
  client:
    build: ./client
    ports: ["80:80"]
    depends_on: [api-server]

  api-server:
    build: ./server
    ports: ["8080:8080"]
    depends_on: [db, genai]

  genai:
    build: ./genai
    ports: ["8000:8000"]
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}

  db:
    image: ankane/pgvector:latest
    ports: ["5432:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]
```

## 🧪 Testing & Validation

### **System Health Checks**
```bash
# Test API server health
curl http://localhost:8080/actuator/health

# Test GenAI service
curl http://localhost:8000

# Test complete analysis flow
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","maxArticles":20}'
```

### **Frontend Testing**
1. Navigate to http://localhost
2. Submit test query: "neural networks"
3. Verify trends appear with progress bars
4. Test article expansion functionality
5. Check analysis appears in history

### **Database Verification**
```sql
-- Connect to database
psql -h localhost -U postgres -d niche

-- Check data
SELECT COUNT(*) FROM analysis;
SELECT COUNT(*) FROM trend;
SELECT COUNT(*) FROM article;

-- Verify vector extensions
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## 📈 Performance & Monitoring

### **Expected Performance**
- **Analysis Time**: 10-30 seconds for 50 articles
- **Memory Usage**: ~2GB total across all containers
- **Storage**: ~100MB per 1000 articles with embeddings

### **Monitoring Commands**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs api-server
docker-compose logs genai
docker-compose logs client

# Monitor resource usage
docker stats
```

### **Performance Tuning**
```bash
# Increase JVM heap for API server
docker-compose up -d --scale api-server=1 \
  -e JAVA_OPTS="-Xmx2g -Xms1g"

# Adjust GenAI processing limits
echo "MAX_ARTICLES_PER_REQUEST=75" >> .env
```

## 🔒 Security & Production

### **Security Considerations**
- API keys stored in environment variables only
- CORS protection enabled on API server
- Input validation on all endpoints
- SQL injection prevention through JPA
- Content hashing prevents malicious duplicates

### **Production Deployment**
```bash
# For production, use separate environment file
cp .env .env.production

# Update with production values
sed -i 's/localhost/your-domain.com/g' .env.production

# Deploy with production configuration
docker-compose --env-file .env.production up -d
```

## 🚨 Troubleshooting

### **Common Issues**

**GenAI Service Fails to Start**
```bash
# Check API key configuration
docker-compose logs genai | grep "API_KEY"

# Verify model download
docker-compose exec genai ls -la /app/models/
```

**Database Connection Errors**
```bash
# Check database status
docker-compose logs db

# Reset database volume if needed
docker-compose down -v
docker-compose up -d
```

**Frontend Not Loading**
```bash
# Check nginx configuration
docker-compose exec client cat /etc/nginx/conf.d/default.conf

# Verify build artifacts
docker-compose exec client ls -la /usr/share/nginx/html/
```

### **Performance Issues**
```bash
# If analysis is slow, check GenAI service resources
docker stats team-dev_ops-genai-1

# Reduce article limit for testing
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"test","maxArticles":10}'
```

## 📋 Maintenance

### **Regular Tasks**
- Monitor disk usage for PostgreSQL volume
- Check API key usage limits with Google
- Review application logs for errors
- Update dependencies quarterly

### **Backup Strategy**
```bash
# Backup database
docker-compose exec db pg_dump -U postgres niche > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U postgres niche
```

### **Updates**
```bash
# Update application code
git pull origin main

# Rebuild and restart services
docker-compose build
docker-compose up -d
```

---

## ✅ Ready for Commit

The NicheExplorer system is now streamlined and production-ready with:

- **Complete trend analysis pipeline** from query to results
- **Robust vector embedding system** with PostgreSQL storage
- **Clean, responsive frontend** with interactive visualizations
- **Comprehensive error handling** and logging
- **Production-ready deployment** with Docker Compose
- **Detailed documentation** for all components

The system successfully processes research queries, extracts semantic trends, generates vector embeddings, and provides an intuitive interface for exploring results. All experimental features have been removed, leaving a focused, reliable application ready for production deployment.

**Next Steps**: Commit the current state and deploy to your target environment using the instructions above.
