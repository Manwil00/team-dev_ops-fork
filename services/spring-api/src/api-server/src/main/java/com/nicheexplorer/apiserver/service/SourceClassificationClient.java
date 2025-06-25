package com.nicheexplorer.apiserver.service;

import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import com.nicheexplorer.apiserver.config.GenAiProperties;

@Component
public class SourceClassificationClient {

    private final WebClient webClient;

    public SourceClassificationClient(WebClient.Builder builder, GenAiProperties props) {
        this.webClient = builder.baseUrl(props.getBaseUrl()).build();
    }

    public ClassificationResponse classify(String query) {
        try {
            return webClient.post()
                    .uri("/classify")
                    .bodyValue(new ClassificationRequest(query))
                    .retrieve()
                    .bodyToMono(ClassificationResponse.class)
                    .block();
        } catch (Exception e) {
            return null;
        }
    }

    public record ClassificationRequest(String query) {}

    public record ClassificationResponse(String source, String feed) {}
} 