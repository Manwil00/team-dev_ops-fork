package com.nicheexplorer.apiserver.model;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;
import org.hibernate.annotations.Array;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "topic")
public class Topic {

    @Id
    private UUID id;

    private String query;

    private String type; // Research or Community

    @Column(name = "feed_url")
    private String feedUrl;

    private String title;

    @Column(columnDefinition = "text")
    private String description;

    private int articleCount;

    private int relevance;

    private Instant createdAt;

    @JdbcTypeCode(SqlTypes.VECTOR)
    @Array(length = 768)
    private float[] embedding;

    // getters and setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getQuery() { return query; }
    public void setQuery(String query) { this.query = query; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getFeedUrl() { return feedUrl; }
    public void setFeedUrl(String feedUrl) { this.feedUrl = feedUrl; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public int getArticleCount() { return articleCount; }
    public void setArticleCount(int articleCount) { this.articleCount = articleCount; }

    public int getRelevance() { return relevance; }
    public void setRelevance(int relevance) { this.relevance = relevance; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public float[] getEmbedding() { return embedding; }
    public void setEmbedding(float[] embedding) { this.embedding = embedding; }
} 