package com.nicheexplorer.apiserver.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nicheexplorer.generated.model.ArticleFetchRequest;
import com.nicheexplorer.generated.model.ArticleFetchResponse;
import com.nicheexplorer.generated.model.ClassifyResponse;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.io.IOException;

import static org.assertj.core.api.Assertions.assertThat;

public class AnalysisOrchestrationServiceTest {

    private static MockWebServer mockGenaiServer;
    private static MockWebServer mockFetcherServer;
    private AnalysisOrchestrationService orchestrationService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @BeforeAll
    static void setUp() throws IOException {
        mockGenaiServer = new MockWebServer();
        mockGenaiServer.start();

        mockFetcherServer = new MockWebServer();
        mockFetcherServer.start();
    }

    @AfterAll
    static void tearDown() throws IOException {
        mockGenaiServer.shutdown();
        mockFetcherServer.shutdown();
    }

    @BeforeEach
    void initialize() {
        String genaiUrl = String.format("http://localhost:%s", mockGenaiServer.getPort());
        String fetcherUrl = String.format("http://localhost:%s", mockFetcherServer.getPort());
        // For this test, we don't need the topics service, so we can point it to any valid URL
        String topicsUrl = fetcherUrl;

        orchestrationService = new AnalysisOrchestrationService(
                WebClient.builder(),
                genaiUrl,
                fetcherUrl,
                topicsUrl
        );
    }

    /**
     * Tests the classifyQuery method.
     *
     * Test Description:
     * This test verifies that the service can correctly call the `py-genai`
     * service to classify a user's query. It uses a MockWebServer to simulate
     * the `py-genai` API.
     *
     * Assertions:
     * - The service method returns a non-null `ClassifyResponse`.
     * - The `source` in the response matches the mock response.
     */
    @Test
    void whenClassifyQuery_thenReturnsClassification() throws JsonProcessingException {
        // Arrange: Set up the mock response from the py-genai service
        var mockResponse = new ClassifyResponse()
                .source(ClassifyResponse.SourceEnum.ARXIV)
                .sourceType(ClassifyResponse.SourceTypeEnum.RESEARCH)
                .suggestedCategory("cs.AI");

        mockGenaiServer.enqueue(new MockResponse()
                .setBody(objectMapper.writeValueAsString(mockResponse))
                .addHeader("Content-Type", "application/json"));

        // Act: Call the service method
        Mono<ClassifyResponse> responseMono = orchestrationService.classifyQuery("test query");

        // Assert: Use StepVerifier for reactive streams
        StepVerifier.create(responseMono)
                .assertNext(response -> {
                    assertThat(response).isNotNull();
                    assertThat(response.getSource()).isEqualTo(ClassifyResponse.SourceEnum.ARXIV);
                })
                .verifyComplete();
    }

    /**
     * Tests the fetchArticles method.
     *
     * Test Description:
     * This test verifies that the service can correctly call the `py-fetcher`
     * service to fetch articles based on a classification result.
     *
     * Assertions:
     * - The service method returns a non-null `ArticleFetchResponse`.
     * - The `totalFound` in the response matches the mock response.
     */
    @Test
    void whenFetchArticles_thenReturnsArticles() throws JsonProcessingException {
        // Arrange: Set up the mock response from the py-fetcher service
        var mockResponse = new ArticleFetchResponse()
                .totalFound(10);

        mockFetcherServer.enqueue(new MockResponse()
                .setBody(objectMapper.writeValueAsString(mockResponse))
                .addHeader("Content-Type", "application/json"));
        
        var classification = new ClassifyResponse()
                .source(ClassifyResponse.SourceEnum.ARXIV)
                .suggestedCategory("cs.AI");

        // Act
        Mono<ArticleFetchResponse> responseMono = orchestrationService.fetchArticles(classification, "test query");

        // Assert
        StepVerifier.create(responseMono)
                .assertNext(response -> {
                    assertThat(response).isNotNull();
                    assertThat(response.getTotalFound()).isEqualTo(10);
                })
                .verifyComplete();
    }
} 