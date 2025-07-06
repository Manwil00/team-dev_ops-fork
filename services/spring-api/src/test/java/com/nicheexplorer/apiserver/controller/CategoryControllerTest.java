package com.nicheexplorer.apiserver.controller;

import com.nicheexplorer.apiserver.service.AnalysisOrchestrationService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

import static org.mockito.Mockito.when;

/**
 * Unit tests for CategoryController.
 *
 * Test Description:
 * This class uses @WebFluxTest to test the controller layer in isolation.
 * The AnalysisOrchestrationService is mocked to verify that the controller
 * correctly handles web requests and calls the service layer as expected.
 */
@WebFluxTest(CategoryController.class)
public class CategoryControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private AnalysisOrchestrationService orchestrationService;

    /**
     * Tests the GET /api/v1/sources/{source}/categories endpoint.
     *
     * Test Description:
     * Verifies that the controller can handle a GET request to fetch categories
     * for a given source, calls the orchestration service, and returns the
     * data with a 200 OK status.
     */
    @Test
    void whenGetSourceCategories_thenReturnsMapOfCategories() {
        // Arrange
        String source = "arxiv";
        Map<String, List<String>> mockCategories = Map.of("Computer Science", List.of("cs.AI"));
        when(orchestrationService.getSourceCategories(source)).thenReturn(Mono.just(mockCategories));

        // Act & Assert
        webTestClient.get().uri("/api/v1/sources/{source}/categories", source)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Map.class)
                .isEqualTo(mockCategories);
    }
} 