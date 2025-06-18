package com.nicheexplorer.apiserver.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.List;

@Service
public class EmbeddingClient {

    private final WebClient webClient;

    public EmbeddingClient(WebClient.Builder builder, @Value("${genai.base-url}") String baseUrl) {
        this.webClient = builder.baseUrl(baseUrl).build();
    }

    public float[] embed(String text) {
        EmbedResponse resp = webClient.post()
                .uri("/embed")
                .bodyValue(new EmbedRequest(text))
                .retrieve()
                .bodyToMono(EmbedResponse.class)
                .onErrorResume(e -> Mono.just(new EmbedResponse(List.of())))
                .block();
        List<Float> vec = resp != null ? resp.vector() : List.of();
        float[] arr = new float[vec.size()];
        for (int i = 0; i < vec.size(); i++) {
            arr[i] = vec.get(i);
        }
        return arr;
    }

    private record EmbedRequest(String text) {}
    private record EmbedResponse(List<Float> vector) {}
} 