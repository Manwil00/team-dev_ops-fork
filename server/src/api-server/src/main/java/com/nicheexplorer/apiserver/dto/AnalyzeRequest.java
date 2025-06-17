package com.nicheexplorer.apiserver.dto;

public class AnalyzeRequest {
    private String query;
    private boolean autoDetect = true;
    private int maxArticles = 50;
    private int trendClusters = 3;

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
} 