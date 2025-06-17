package com.nicheexplorer.apiserver.dto;

public class TrendDto {
    private String id;
    private String title;
    private String description;
    private int articleCount;
    private int relevance;
    private java.util.List<ArticleDto> articles;

    public TrendDto() {
    }

    public TrendDto(String id, String title, String description, int articleCount, int relevance, java.util.List<ArticleDto> articles) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.articleCount = articleCount;
        this.relevance = relevance;
        this.articles = articles;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public int getArticleCount() {
        return articleCount;
    }

    public void setArticleCount(int articleCount) {
        this.articleCount = articleCount;
    }

    public int getRelevance() {
        return relevance;
    }

    public void setRelevance(int relevance) {
        this.relevance = relevance;
    }

    public java.util.List<ArticleDto> getArticles() {
        return articles;
    }

    public void setArticles(java.util.List<ArticleDto> articles) {
        this.articles = articles;
    }
} 