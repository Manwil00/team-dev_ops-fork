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

/**
 * Client for communicating with the topic-discovery micro-service.
 * It implements the three-step orchestrated flow:
 *   1. Call genai /arxiv/search  ➜ list of articles
 *   2. Call genai /embed-batch   ➜ cache vectors
 *   3. Call topic-discovery /discover-topic ➜ clustered topics
 */
@Service
public class TopicDiscoveryClient {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${topic.base-url}")
    private String topicBaseUrl;

    @Value("${genai.base-url}")
    private String genaiBaseUrl;

    /**
     * Main entry point used by AnalysisService.
     */
    public TrendsResponse discoverTopic(String query, String feedUrl, int maxArticles, int minFrequency) {
        try {
            // 1️⃣  Fetch papers from arXiv via GenAI service
            String arxivUrl = genaiBaseUrl + "/arxiv/search";
            HttpHeaders headers = jsonHeaders();
            Map<String, Object> arxivRequest = new HashMap<>();
            arxivRequest.put("query", feedUrl);
            arxivRequest.put("max_results", maxArticles);
            ResponseEntity<Map> arxivResponse = restTemplate.postForEntity(arxivUrl, new HttpEntity<>(arxivRequest, headers), Map.class);
            List<Map<String, Object>> articles = (List<Map<String, Object>>) arxivResponse.getBody().get("articles");

            // collect IDs
            List<String> articleIds = new ArrayList<>();
            for (Map<String, Object> article : articles) {
                articleIds.add((String) article.get("id"));
            }

            // 2️⃣  Generate & cache embeddings
            String embedUrl = genaiBaseUrl + "/embed-batch";
            Map<String, Object> embedRequest = new HashMap<>();
            List<String> texts = new ArrayList<>();
            for (Map<String, Object> article : articles) {
                texts.add(article.get("title") + ". " + article.get("abstract"));
            }
            embedRequest.put("texts", texts);
            embedRequest.put("ids", articleIds);
            restTemplate.postForEntity(embedUrl, new HttpEntity<>(embedRequest, headers), Map.class);

            // 3️⃣  Discover clustered topics
            String topicUrl = topicBaseUrl + "/discover-topic";
            Map<String, Object> topicRequest = new HashMap<>();
            topicRequest.put("query", query);
            topicRequest.put("article_keys", articleIds);
            topicRequest.put("articles", articles);
            topicRequest.put("min_cluster_size", minFrequency);

            ResponseEntity<TrendsResponse> topicResponse = restTemplate.postForEntity(topicUrl, new HttpEntity<>(topicRequest, headers), TrendsResponse.class);
            return topicResponse.getBody();
        } catch (Exception e) {
            throw new RuntimeException("Topic discovery flow failed", e);
        }
    }

    private HttpHeaders jsonHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        return headers;
    }

    /*——————————————————————————————————– DTOs ——————————————————————————————————*/
    public static class TrendsResponse {
        private String query;
        private String feed_url;
        private List<Topic> trends;
        private int total_articles_processed;

        // getters & setters
        public String getQuery() { return query; }
        public void setQuery(String query) { this.query = query; }
        public String getFeed_url() { return feed_url; }
        public void setFeed_url(String feed_url) { this.feed_url = feed_url; }
        public List<Topic> getTrends() { return trends; }
        public void setTrends(List<Topic> trends) { this.trends = trends; }
        public int getTotal_articles_processed() { return total_articles_processed; }
        public void setTotal_articles_processed(int total_articles_processed) { this.total_articles_processed = total_articles_processed; }
    }

    public static class Topic {
        private String id;
        private String title;
        private String description;
        private int article_count;
        private int relevance;
        private List<Map<String, Object>> articles;
        // getters & setters
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