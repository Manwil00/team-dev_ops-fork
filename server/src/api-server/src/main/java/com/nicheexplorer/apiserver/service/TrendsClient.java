package com.nicheexplorer.apiserver.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.HashMap;

@Service
public class TrendsClient {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${topic.base-url}")
    private String topicBaseUrl;
    
    @Value("${genai.base-url}")
    private String genaiBaseUrl;

    public TrendsResponse discoverTopics(String query, String feedUrl, int maxArticles, int minFrequency) {
        String url = topicBaseUrl + "/topic-discovery";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        TrendsRequest request = new TrendsRequest(query, feedUrl, maxArticles, minFrequency);
        HttpEntity<TrendsRequest> entity = new HttpEntity<>(request, headers);

        try {
            ResponseEntity<TrendsResponse> response = restTemplate.postForEntity(url, entity, TrendsResponse.class);
            return response.getBody();
        } catch (Exception e) {
            throw new RuntimeException("Failed to discover topics from GenAI service", e);
        }
    }

    public TrendsResponse discoverTopicsProperFlow(String query, String feedUrl, int maxArticles, int minFrequency) {
        try {
            // Step 1: Fetch papers by arXiv category using GenAI service arXiv router
            String arxivUrl = genaiBaseUrl + "/arxiv/search";
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            // Create request for arXiv search
            Map<String, Object> arxivRequest = new HashMap<>();
            arxivRequest.put("query", feedUrl); // Use category (cs.CV) as query
            arxivRequest.put("max_results", maxArticles);
            
            HttpEntity<Map<String, Object>> arxivEntity = new HttpEntity<>(arxivRequest, headers);
            ResponseEntity<Map> arxivResponse = restTemplate.postForEntity(arxivUrl, arxivEntity, Map.class);
            
            List<Map<String, Object>> articles = (List<Map<String, Object>>) arxivResponse.getBody().get("articles");
            List<String> articleIds = new ArrayList<>();
            
            // Extract article IDs
            for (Map<String, Object> article : articles) {
                articleIds.add((String) article.get("id"));
            }
            
            // Step 2: Generate and cache embeddings using GenAI batch endpoint
            String embedUrl = genaiBaseUrl + "/embed-batch";
            Map<String, Object> embedRequest = new HashMap<>();
            
            List<String> texts = new ArrayList<>();
            for (Map<String, Object> article : articles) {
                texts.add(article.get("title") + ". " + article.get("abstract"));
            }
            
            embedRequest.put("texts", texts);
            embedRequest.put("ids", articleIds);
            
            HttpEntity<Map<String, Object>> embedEntity = new HttpEntity<>(embedRequest, headers);
            restTemplate.postForEntity(embedUrl, embedEntity, Map.class); // Just cache, don't need response
            
            // Step 3: Discover topics from cached embeddings
            String topicUrl = topicBaseUrl + "/discover-topics-from-embeddings";
            Map<String, Object> topicRequest = new HashMap<>();
            topicRequest.put("query", query);
            topicRequest.put("article_keys", articleIds);
            topicRequest.put("articles", articles);
            topicRequest.put("min_cluster_size", minFrequency);
            
            HttpEntity<Map<String, Object>> topicEntity = new HttpEntity<>(topicRequest, headers);
            ResponseEntity<TrendsResponse> topicResponse = restTemplate.postForEntity(topicUrl, topicEntity, TrendsResponse.class);
            
            return topicResponse.getBody();
            
        } catch (Exception e) {
            // Fallback to old method if proper flow fails
            System.err.println("Proper flow failed, falling back to old method: " + e.getMessage());
            return discoverTopics(query, feedUrl, maxArticles, minFrequency);
        }
    }

    public static class TrendsRequest {
        private String query;
        private String feed_url;  // Use snake_case to match Python API
        private int max_articles; // Use snake_case to match Python API
        private int min_frequency; // Use snake_case to match Python API

        public TrendsRequest() {}

        public TrendsRequest(String query, String feedUrl, int maxArticles, int minFrequency) {
            this.query = query;
            this.feed_url = feedUrl;
            this.max_articles = maxArticles;
            this.min_frequency = minFrequency;
        }

        // Getters and setters with snake_case field names
        public String getQuery() { return query; }
        public void setQuery(String query) { this.query = query; }
        
        public String getFeed_url() { return feed_url; }
        public void setFeed_url(String feed_url) { this.feed_url = feed_url; }
        
        public int getMax_articles() { return max_articles; }
        public void setMax_articles(int max_articles) { this.max_articles = max_articles; }
        
        public int getMin_frequency() { return min_frequency; }
        public void setMin_frequency(int min_frequency) { this.min_frequency = min_frequency; }
    }

    public static class TrendsResponse {
        private String query;
        private String feed_url;
        private List<TrendTopic> trends;
        private int total_articles_processed;

        // Getters and setters
        public String getQuery() { return query; }
        public void setQuery(String query) { this.query = query; }
        
        public String getFeed_url() { return feed_url; }
        public void setFeed_url(String feed_url) { this.feed_url = feed_url; }
        
        public List<TrendTopic> getTrends() { return trends; }
        public void setTrends(List<TrendTopic> trends) { this.trends = trends; }
        
        public int getTotal_articles_processed() { return total_articles_processed; }
        public void setTotal_articles_processed(int total_articles_processed) { 
            this.total_articles_processed = total_articles_processed; 
        }
    }

    public static class TrendTopic {
        private String id;
        private String title;
        private String description;
        private int article_count;
        private int relevance;
        private List<Map<String, Object>> articles;

        // Getters and setters
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        
        public String getTitle() { return title; }
        public void setTitle(String title) { this.title = title; }
        
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        
        public int getArticle_count() { return article_count; }
        public void setArticle_count(int article_count) { this.article_count = article_count; }
        
        public int getRelevance() { return relevance; }
        public void setRelevance(int relevance) { this.relevance = relevance; }
        
        public List<Map<String, Object>> getArticles() { return articles; }
        public void setArticles(List<Map<String, Object>> articles) { this.articles = articles; }
    }
} 