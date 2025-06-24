package com.nicheexplorer.apiserver.dto;

import java.time.Instant;
import java.util.List;
import com.nicheexplorer.apiserver.dto.TopicDto;

public class AnalysisResponse {
    private String id;
    private String query;
    private Instant timestamp;
    private String type;
    private List<TopicDto> trends;
    private String feedUrl;

    public AnalysisResponse() {
    }

    public AnalysisResponse(String id, String query, Instant timestamp, String type, List<TopicDto> trends, String feedUrl) {
        this.id = id;
        this.query = query;
        this.timestamp = timestamp;
        this.type = type;
        this.trends = trends;
        this.feedUrl = feedUrl;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getQuery() {
        return query;
    }

    public void setQuery(String query) {
        this.query = query;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public List<TopicDto> getTrends() {
        return trends;
    }

    public void setTrends(List<TopicDto> trends) {
        this.trends = trends;
    }

    public String getFeedUrl() {
        return feedUrl;
    }

    public void setFeedUrl(String feedUrl) {
        this.feedUrl = feedUrl;
    }
} 