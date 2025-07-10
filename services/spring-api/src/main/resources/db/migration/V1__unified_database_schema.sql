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
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    feed_url TEXT NOT NULL,
    total_articles_processed INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT now()
);

-- Create topic table with proper relationships
CREATE TABLE topic (
    id UUID PRIMARY KEY,
    analysis_id UUID NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    article_count INT DEFAULT 0,
    relevance INT DEFAULT 0,
    CONSTRAINT fk_topic_analysis FOREIGN KEY (analysis_id) REFERENCES analysis(id) ON DELETE CASCADE
);

-- Create article table to store individual articles (deduplicated globally, not per analysis)
CREATE TABLE article (
    id UUID PRIMARY KEY,
    external_id TEXT NOT NULL,
    title TEXT,
    link TEXT,
    snippet TEXT,
    embedding vector(768),
    CONSTRAINT unique_article_external UNIQUE (external_id)
);

-- Link table to associate articles with multiple topics (many-to-many)
CREATE TABLE topic_article (
    topic_id UUID NOT NULL,
    article_id UUID NOT NULL,
    PRIMARY KEY (topic_id, article_id),
    CONSTRAINT fk_ta_topic FOREIGN KEY (topic_id) REFERENCES topic(id) ON DELETE CASCADE,
    CONSTRAINT fk_ta_article FOREIGN KEY (article_id) REFERENCES article(id) ON DELETE CASCADE
);

-- Performance indexes for analysis table
CREATE INDEX idx_analysis_created_at ON analysis(created_at DESC);
CREATE INDEX idx_analysis_query ON analysis(query);
CREATE INDEX idx_analysis_type ON analysis(type);

-- Performance indexes for topic table
CREATE INDEX idx_topic_analysis_id ON topic(analysis_id);
CREATE INDEX idx_topic_relevance ON topic(relevance DESC);

-- Performance indexes for article table
CREATE INDEX idx_article_external_id ON article(external_id);

-- Link table index
CREATE INDEX idx_ta_topic ON topic_article(topic_id);

-- Vector similarity search indexes (using IVFFlat for cosine similarity)
CREATE INDEX IF NOT EXISTS article_embedding_idx
    ON article USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Comments for documentation
COMMENT ON TABLE analysis IS 'Tracks complete analysis sessions with metadata about the query and source';
COMMENT ON COLUMN analysis.status IS 'Current status of the analysis job (e.g., PENDING, COMPLETED, FAILED)';
COMMENT ON TABLE topic IS 'Individual topics discovered within an analysis';
COMMENT ON TABLE article IS 'Individual articles that are globally unique by external_id and can be shared across analyses';
