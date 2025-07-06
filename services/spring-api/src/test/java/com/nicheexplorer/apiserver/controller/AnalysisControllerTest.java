package com.nicheexplorer.apiserver.controller;

import com.nicheexplorer.apiserver.service.AnalysisService;
import com.nicheexplorer.generated.model.AnalyzeRequest;
import com.nicheexplorer.generated.model.AnalysisResponse;
import com.nicheexplorer.generated.model.ListAnalyses200Response;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.util.UriComponentsBuilder;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Unit tests for AnalysisController.
 *
 * Test Description:
 * This class uses @WebFluxTest to test the controller layer in isolation.
 * The AnalysisService is mocked to verify that the controller correctly
 * handles web requests and calls the service layer as expected.
 */
@WebFluxTest(AnalysisController.class)
public class AnalysisControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private AnalysisService analysisService;

    /**
     * Tests the POST /api/v1/analyses endpoint.
     *
     * Test Description:
     * Verifies that the controller can accept a POST request to start an analysis,
     * calls the underlying service, and returns a 202 Accepted status.
     */
    @Test
    void whenPostAnalyses_thenReturnsAccepted() {
        webTestClient.post().uri("/api/v1/analyses")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(new AnalyzeRequest().query("test"))
                .exchange()
                .expectStatus().isAccepted();

        verify(analysisService).startAnalysis(any(AnalyzeRequest.class));
    }

    /**
     * Tests the GET /api/v1/analyses endpoint.
     *
     * Test Description:
     * Verifies that the controller can handle a GET request to list analyses,
     * calls the service to fetch the data, and returns it with a 200 OK status.
     */
    @Test
    void whenGetAnalyses_thenReturnsListOfAnalyses() {
        // Arrange
        when(analysisService.countAnalyses()).thenReturn(1);
        when(analysisService.getAnalyses(anyInt(), anyInt())).thenReturn(List.of(new AnalysisResponse()));

        // Act & Assert
        webTestClient.get().uri("/api/v1/analyses?limit=10&offset=0")
                .exchange()
                .expectStatus().isOk()
                .expectBody(ListAnalyses200Response.class);

        verify(analysisService).getAnalyses(10, 0);
    }

    /**
     * Tests the GET /api/v1/analyses/{id} endpoint.
     *
     * Test Description:
     * Verifies that the controller can retrieve a single analysis by its ID.
     */
    @Test
    void whenGetAnalysisById_thenReturnsAnalysis() {
        // Arrange
        UUID id = UUID.randomUUID();
        when(analysisService.getAnalysisById(anyString())).thenReturn(new AnalysisResponse().id(id));

        // Act & Assert
        webTestClient.get().uri("/api/v1/analyses/{id}", id.toString())
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.id").isEqualTo(id.toString());

        verify(analysisService).getAnalysisById(id.toString());
    }

    /**
     * Tests the DELETE /api/v1/analyses/{id} endpoint.
     *
     * Test Description:
     * Verifies that the controller can handle a DELETE request and calls the
     * service to perform the deletion.
     */
    @Test
    void whenDeleteAnalysis_thenReturnsNoContent() {
        // Arrange
        String id = UUID.randomUUID().toString();

        // Act & Assert
        webTestClient.delete().uri("/api/v1/analyses/{id}", id)
                .exchange()
                .expectStatus().isNoContent();

        verify(analysisService).deleteAnalysis(id);
    }
} 