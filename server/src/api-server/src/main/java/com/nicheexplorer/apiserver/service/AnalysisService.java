package com.nicheexplorer.apiserver.service;

import com.nicheexplorer.apiserver.dto.AnalyzeRequest;
import com.nicheexplorer.apiserver.dto.AnalysisResponse;
import com.nicheexplorer.apiserver.dto.TrendDto;
import com.nicheexplorer.apiserver.dto.ArticleDto;
import org.springframework.stereotype.Service;
import com.nicheexplorer.apiserver.service.SourceClassificationClient.ClassificationResponse;
import org.springframework.jdbc.core.JdbcTemplate;
import com.pgvector.PGvector;

import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.nio.charset.StandardCharsets;

@Service
public class AnalysisService {

    // Using Python NLP service for intelligent trend extraction instead of manual stop words

    private final SourceClassificationClient classifier;
    private final JdbcTemplate jdbc;
    private final TrendsClient trendsClient;
    private final EmbeddingClient embedClient;

    public AnalysisService(SourceClassificationClient classifier,
                           JdbcTemplate jdbc,
                           TrendsClient trendsClient,
                           EmbeddingClient embedClient) {
        this.classifier = classifier;
        this.jdbc = jdbc;
        this.trendsClient = trendsClient;
        this.embedClient = embedClient;
    }

    public AnalysisResponse analyze(AnalyzeRequest request) {
        boolean hasManual = request.getSource() != null && !request.getSource().isBlank()
                && request.getFeed() != null && !request.getFeed().isBlank();

        String type;
        String feedId;

        if (hasManual) {
            type = "community".equalsIgnoreCase(request.getSource()) ? "Community" : "Research";
            feedId = request.getFeed();
        } else {
        ClassificationResponse cls = classifier.classify(request.getQuery());
            type = cls != null && "community".equalsIgnoreCase(cls.source()) ? "Community" : "Research";
            feedId = cls != null ? cls.feed() : (type.equals("Research") ? "cs.CV" : "computervision");
        }
        // For research queries, use ArXiv API format; for community, keep RSS
        String feedUrl;
        if (type.equals("Research")) {
            // Check if feedId is already an advanced ArXiv query
            if (feedId.contains("+") || feedId.contains(":")) {
                feedUrl = feedId;  // Use advanced query as-is
            } else {
                feedUrl = "cat:" + feedId;  // Convert simple category to ArXiv API format
            }
        } else {
            feedUrl = "https://www.reddit.com/r/" + feedId + ".rss";
        }

        // Implement proper REST architecture flow:
        // 1. Fetch papers by category from arXiv
        // 2. Generate and cache embeddings in ChromaDB
        // 3. Discover topics from cached embeddings
        TrendsClient.TrendsResponse trendsResponse = trendsClient.discoverTopicsProperFlow(
            request.getQuery(),
            feedUrl, 
            request.getMaxArticles(), 
            3  // min frequency
        );
        
        // Convert Python trends to our DTOs - use all trends found by LangChain clustering
        System.out.println("GenAI response has " + (trendsResponse.getTrends() != null ? trendsResponse.getTrends().size() : "null") + " trends");
        List<TrendDto> trends = trendsResponse.getTrends().stream()
            .map(topic -> {
                // Convert Python articles to ArticleDto
                List<ArticleDto> articles = topic.getArticles().stream()
                    .map(articleMap -> new ArticleDto(
                        UUID.randomUUID().toString(),
                        (String) articleMap.get("title"),
                        (String) articleMap.get("link"),
                        (String) articleMap.get("abstract")  // Python service uses "abstract" field
                    ))
                .collect(Collectors.toList());

                return new TrendDto(
                    UUID.randomUUID().toString(),  // Generate new UUID instead of using Python ID
                    topic.getTitle(),
                    topic.getDescription(),
                    articles.size(),  // Use actual article count instead of GenAI count
                    topic.getRelevance(),
                    articles
                );
            })
            .collect(Collectors.toList());

        // Generate analysis ID and save complete analysis to database
        String analysisId = UUID.randomUUID().toString();
        Instant timestamp = Instant.now();
        
        AnalysisResponse response = new AnalysisResponse(
                analysisId,
                request.getQuery(),
                timestamp,
                type,
                trends,
                feedUrl);

        // Save complete analysis with all trends
        saveAnalysis(analysisId, request.getQuery(), type, feedUrl, trends, timestamp, 
                    trendsResponse.getTotal_articles_processed());
        return response;
    }

    // Removed manual keyword extraction methods - now using Python NLP service

    /**
     * Save complete analysis with all trends and articles with proper relationships
     */
    private void saveAnalysis(String analysisId, String query, String type, String feedUrl, 
                             List<TrendDto> trends, Instant timestamp, int totalArticlesProcessed) {
        
        // 1. Insert analysis record
        String analysisSql = """
            INSERT INTO analysis(id, query, type, feed_url, total_articles_processed, created_at)
            VALUES (?,?,?,?,?,?) ON CONFLICT (id) DO NOTHING
            """;
        
        jdbc.update(analysisSql,
            UUID.fromString(analysisId),
            query,
            type,
            feedUrl,
            totalArticlesProcessed,
            java.sql.Timestamp.from(timestamp));

        // 2. Insert trends linked to this analysis
        String trendSql = """
            INSERT INTO trend(id, query, type, feed_url, title, description, article_count, relevance, created_at, analysis_id)
            VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT (id) DO NOTHING
            """;
        
        for (TrendDto dto : trends) {
            // Skip embedding generation - embeddings are handled by the topic discovery service's vector database
            jdbc.update(trendSql,
                UUID.fromString(dto.getId()),
                query,
                type,
                feedUrl,
                dto.getTitle(),
                dto.getDescription(),
                dto.getArticleCount(),
                dto.getRelevance(),
                java.sql.Timestamp.from(timestamp),
                UUID.fromString(analysisId));
            
            // 4. Save individual articles for this trend
            System.out.println("Saving articles for trend: " + dto.getTitle() + " with " + dto.getArticles().size() + " articles");
            saveArticlesForTrend(dto.getId(), analysisId, dto.getArticles(), timestamp);
        }
    }
    
    /**
     * Save individual articles for a trend with their embeddings
     */
    private void saveArticlesForTrend(String trendId, String analysisId, List<ArticleDto> articles, Instant timestamp) {
        String articleSql = """
            INSERT INTO article(id, trend_id, analysis_id, title, link, snippet, content_hash, created_at)
            VALUES (?,?,?,?,?,?,?,?) ON CONFLICT (trend_id, content_hash) DO NOTHING
            """;
        
        for (ArticleDto article : articles) {
            // Create content hash to prevent duplicates
            String content = article.getTitle() + " " + (article.getSnippet() != null ? article.getSnippet() : "");
            String contentHash;
            try {
                MessageDigest md = MessageDigest.getInstance("SHA-256");
                byte[] hash = md.digest(content.getBytes(StandardCharsets.UTF_8));
                contentHash = java.util.HexFormat.of().formatHex(hash);
            } catch (NoSuchAlgorithmException e) {
                // Fallback to hashCode if SHA-256 fails
                contentHash = String.valueOf(content.hashCode());
            }
            
            try {
                // Insert article
                jdbc.update(articleSql,
                    UUID.fromString(article.getId()),
                    UUID.fromString(trendId),
                    UUID.fromString(analysisId),
                    article.getTitle(),
                    article.getLink(),
                    article.getSnippet(),
                    contentHash,
                    java.sql.Timestamp.from(timestamp));
                
                // Skip embedding generation - embeddings are handled by the topic discovery service's vector database
            } catch (Exception e) {
                // Log error but continue with other articles
                System.err.println("Error saving article " + article.getId() + ": " + e.getMessage());
            }
        }
    }

    /**
     * Get complete analysis history with all trends
     */
    public List<AnalysisResponse> getAnalysisHistory(String queryFilter, int limit) {
        String sql;
        Object[] params;
        
        if (queryFilter != null && !queryFilter.trim().isEmpty()) {
            sql = """
                SELECT a.id, a.query, a.type, a.feed_url, a.created_at, a.total_articles_processed
                FROM analysis a 
                WHERE a.query ILIKE ?
                ORDER BY a.created_at DESC
                LIMIT ?
                """;
            params = new Object[]{"%" + queryFilter + "%", limit};
        } else {
            sql = """
                SELECT a.id, a.query, a.type, a.feed_url, a.created_at, a.total_articles_processed  
                FROM analysis a
                ORDER BY a.created_at DESC
                LIMIT ?
                """;
            params = new Object[]{limit};
        }
        
        List<AnalysisResponse> analyses = jdbc.query(sql,
            (rs, rowNum) -> {
                String analysisId = rs.getString("id");
                
                // Get trends for this analysis
                List<TrendDto> trends = getTrendsForAnalysis(analysisId);
                
                return new AnalysisResponse(
                    analysisId,
                    rs.getString("query"),
                    rs.getTimestamp("created_at").toInstant(),
                    rs.getString("type"),
                    trends,
                    rs.getString("feed_url")
                );
            },
            params);
            
        return analyses;
    }
    
    /**
     * Get trends for a specific analysis with their articles
     */
    private List<TrendDto> getTrendsForAnalysis(String analysisId) {
        String sql = """
            SELECT id, title, description, article_count, relevance
            FROM trend 
            WHERE analysis_id = ?
            ORDER BY relevance DESC
            """;
        
        return jdbc.query(sql,
            (rs, rowNum) -> {
                String trendId = rs.getString("id");
                List<ArticleDto> articles = getArticlesForTrend(trendId);
                
                return new TrendDto(
                    trendId,
                    rs.getString("title"),
                    rs.getString("description"),
                    articles.size(),  // Use actual article count instead of stored value
                    rs.getInt("relevance"),
                    articles
                );
            },
            UUID.fromString(analysisId));
    }
    
    /**
     * Get articles for a specific trend
     */
    private List<ArticleDto> getArticlesForTrend(String trendId) {
        String sql = """
            SELECT id, title, link, snippet
            FROM article 
            WHERE trend_id = ?
            ORDER BY created_at
            """;
        
        return jdbc.query(sql,
            (rs, rowNum) -> new ArticleDto(
                rs.getString("id"),
                rs.getString("title"),
                rs.getString("link"),
                rs.getString("snippet")
            ),
            UUID.fromString(trendId));
    }

    /**
     * Get vector embedding for a trend
     */
    public Map<String, Object> getTrendEmbedding(String trendId) {
        String sql = """
            SELECT title, description, embedding
            FROM trend 
            WHERE id = ?
            """;
        
        return jdbc.query(sql,
            rs -> {
                if (rs.next()) {
                    Map<String, Object> result = new HashMap<>();
                    result.put("id", trendId);
                    result.put("title", rs.getString("title"));
                    result.put("description", rs.getString("description"));
                    
                    Object embedding = rs.getObject("embedding");
                    if (embedding != null) {
                        result.put("embedding", embedding.toString());
                        result.put("has_embedding", true);
                    } else {
                        result.put("has_embedding", false);
                    }
                    return result;
                }
                return null;
            },
            UUID.fromString(trendId));
    }
    
    /**
     * Get vector embedding for an article
     */
    public Map<String, Object> getArticleEmbedding(String articleId) {
        String sql = """
            SELECT title, link, snippet, embedding
            FROM article 
            WHERE id = ?
            """;
        
        return jdbc.query(sql,
            rs -> {
                if (rs.next()) {
                    Map<String, Object> result = new HashMap<>();
                    result.put("id", articleId);
                    result.put("title", rs.getString("title"));
                    result.put("link", rs.getString("link"));
                    result.put("snippet", rs.getString("snippet"));
                    
                    Object embedding = rs.getObject("embedding");
                    if (embedding != null) {
                        result.put("embedding", embedding.toString());
                        result.put("has_embedding", true);
                    } else {
                        result.put("has_embedding", false);
                    }
                    return result;
                }
                return null;
            },
            UUID.fromString(articleId));
    }
    
    /**
     * Find similar trends based on vector similarity
     */
    public List<Map<String, Object>> findSimilarTrends(String trendId, int limit) {
        String sql = """
            SELECT t1.id, t1.title, t1.description, t1.relevance,
                   (t1.embedding <=> t2.embedding) as similarity_distance
            FROM trend t1, trend t2
            WHERE t2.id = ? AND t1.id != ?
            ORDER BY t1.embedding <=> t2.embedding
            LIMIT ?
            """;
        
        return jdbc.query(sql,
            (rs, rowNum) -> {
                Map<String, Object> result = new HashMap<>();
                result.put("id", rs.getString("id"));
                result.put("title", rs.getString("title"));
                result.put("description", rs.getString("description"));
                result.put("relevance", rs.getInt("relevance"));
                result.put("similarity_score", 1.0 - rs.getDouble("similarity_distance")); // Convert distance to similarity
                return result;
            },
            UUID.fromString(trendId), UUID.fromString(trendId), limit);
    }

    /**
     * Delete an analysis and all its associated trends and articles
     */
    public void deleteAnalysis(String analysisId) {
        // Delete articles first (due to foreign key constraints)
        String deleteArticlesSql = "DELETE FROM article WHERE analysis_id = ?";
        jdbc.update(deleteArticlesSql, UUID.fromString(analysisId));
        
        // Delete trends (this will also cascade to articles if not already deleted)
        String deleteTrendsSql = "DELETE FROM trend WHERE analysis_id = ?";
        jdbc.update(deleteTrendsSql, UUID.fromString(analysisId));
        
        // Delete the analysis
        String deleteAnalysisSql = "DELETE FROM analysis WHERE id = ?";
        jdbc.update(deleteAnalysisSql, UUID.fromString(analysisId));
    }
} 