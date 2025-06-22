-- Unified Database Schema for Niche Explorer Platform
-- This migration creates the complete database schema in one go
-- Combines functionality from V1, V2, and V3 migrations

-- Enable vector extension for pgvector support
CREATE EXTENSION IF NOT EXISTS vector;

-- Create analysis table to track complete analysis sessions
CREATE TABLE analysis (
    id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'Research' or 'Community'
    feed_url TEXT NOT NULL,
    total_articles_processed INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT now()
);

-- Create trend table with proper relationships
CREATE TABLE trend (
    id UUID PRIMARY KEY,
    analysis_id UUID NOT NULL,
    query VARCHAR(255),
    type VARCHAR(50),
    feed_url TEXT,
    title TEXT NOT NULL,
    description TEXT,
    article_count INT DEFAULT 0,
    relevance INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    embedding vector(768), -- Using 768-dimensional embeddings (compatible with all-MiniLM-L6-v2)
    
    -- Foreign key relationship to analysis table
    CONSTRAINT fk_trend_analysis 
        FOREIGN KEY (analysis_id) REFERENCES analysis(id) ON DELETE CASCADE
);

-- Create article table to store individual articles
CREATE TABLE article (
    id UUID PRIMARY KEY,
    trend_id UUID NOT NULL,
    analysis_id UUID NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    snippet TEXT,
    content_hash VARCHAR(64), -- SHA-256 hash to prevent duplicates
    created_at TIMESTAMP DEFAULT now(),
    embedding vector(768), -- Vector embedding of article content
    
    -- Foreign key relationships
    CONSTRAINT fk_article_trend 
        FOREIGN KEY (trend_id) REFERENCES trend(id) ON DELETE CASCADE,
    CONSTRAINT fk_article_analysis 
        FOREIGN KEY (analysis_id) REFERENCES analysis(id) ON DELETE CASCADE,
    
    -- Prevent duplicate articles per trend
    CONSTRAINT unique_article_per_trend UNIQUE (trend_id, content_hash)
);

-- Performance indexes for analysis table
CREATE INDEX idx_analysis_created_at ON analysis(created_at DESC);
CREATE INDEX idx_analysis_query ON analysis(query);
CREATE INDEX idx_analysis_type ON analysis(type);

-- Performance indexes for trend table
CREATE INDEX idx_trend_analysis_id ON trend(analysis_id);
CREATE INDEX idx_trend_created_at ON trend(created_at DESC);
CREATE INDEX idx_trend_relevance ON trend(relevance DESC);

-- Performance indexes for article table
CREATE INDEX idx_article_trend_id ON article(trend_id);
CREATE INDEX idx_article_analysis_id ON article(analysis_id);
CREATE INDEX idx_article_created_at ON article(created_at DESC);
CREATE INDEX idx_article_content_hash ON article(content_hash);

-- Vector similarity search indexes (using IVFFlat for cosine similarity)
CREATE INDEX trend_embedding_idx ON trend USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100); -- Optimize for up to ~10,000 vectors

CREATE INDEX article_embedding_idx ON article USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100); -- Optimize for up to ~10,000 vectors

-- Comments for documentation
COMMENT ON TABLE analysis IS 'Tracks complete analysis sessions with metadata about the query and source';
COMMENT ON TABLE trend IS 'Individual trends discovered within an analysis, with vector embeddings for similarity search';
COMMENT ON TABLE article IS 'Individual articles that belong to trends, with their own vector embeddings';
COMMENT ON COLUMN trend.embedding IS '768-dimensional vector embedding for semantic similarity search using Google Gemini';
COMMENT ON COLUMN article.embedding IS '768-dimensional vector embedding of article content for detailed similarity search';
COMMENT ON INDEX trend_embedding_idx IS 'IVFFlat index for fast cosine similarity search on trend embeddings';
COMMENT ON INDEX article_embedding_idx IS 'IVFFlat index for fast cosine similarity search on article embeddings'; 