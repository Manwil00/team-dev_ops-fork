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

@Service
public class TrendsClient {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${genai.base-url}")
    private String genaiBaseUrl;

    public TrendsResponse discoverTopics(String query, String feedUrl, int maxArticles, int minFrequency) {
        String url = genaiBaseUrl + "/topic-discovery";

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