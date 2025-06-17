package com.nicheexplorer.apiserver.service;

import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import com.nicheexplorer.apiserver.config.GenAiProperties;

@Component
public class TrendExplainClient {
    private final WebClient webClient;

    public TrendExplainClient(WebClient.Builder builder, GenAiProperties props) {
        this.webClient = builder.baseUrl(props.getBaseUrl()).build();
    }

    public String explain(String keyword, java.util.List<String> titles) {
        try {
            return webClient.post()
                    .uri("/describe")
                    .bodyValue(new DescribeRequest(keyword, titles))
                    .retrieve()
                    .bodyToMono(DescribeResponse.class)
                    .blockOptional()
                    .map(DescribeResponse::description)
                    .orElse("No explanation available");
        } catch (Exception e) {
            return "No explanation available";
        }
    }

    public record DescribeRequest(String keyword, java.util.List<String> titles) {}
    public record DescribeResponse(String description) {}
} 