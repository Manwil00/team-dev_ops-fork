package com.nicheexplorer.apiserver.dto;

public class AnalyzeRequest {
    private String query;
    private boolean autoDetect = true;
    private int maxArticles = 50;
    private int trendClusters = 3;
    private String source; // optional manual override: "research" or "community"
    private String feed;   // optional manual override, e.g. "cs.CV" or "computervision"

    public AnalyzeRequest() {}

    public String getQuery() {
        return query;
    }

    public void setQuery(String query) {
        this.query = query;
    }

    public boolean isAutoDetect() {
        return autoDetect;
    }

    public void setAutoDetect(boolean autoDetect) {
        this.autoDetect = autoDetect;
    }

    public int getMaxArticles() {
        return maxArticles;
    }

    public void setMaxArticles(int maxArticles) {
        this.maxArticles = maxArticles;
    }

    public int getTrendClusters() {
        return trendClusters;
    }

    public void setTrendClusters(int trendClusters) {
        this.trendClusters = trendClusters;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getFeed() {
        return feed;
    }

    public void setFeed(String feed) {
        this.feed = feed;
    }
} 