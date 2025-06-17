package com.nicheexplorer.apiserver.dto;

public class ArticleDto {
    private String id;
    private String title;
    private String link;
    private String snippet;

    public ArticleDto() {}

    public ArticleDto(String id, String title, String link, String snippet) {
        this.id = id;
        this.title = title;
        this.link = link;
        this.snippet = snippet;
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

    public String getLink() {
        return link;
    }

    public void setLink(String link) {
        this.link = link;
    }

    public String getSnippet() {
        return snippet;
    }

    public void setSnippet(String snippet) {
        this.snippet = snippet;
    }
} 