package com.nicheexplorer.apiserver;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.TestPropertySource;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@TestPropertySource(properties = {
    "genai.base-url=http://localhost:8000",
    "topic.base-url=http://localhost:8100"
})
class AnalysisControllerTest {

    @LocalServerPort
    private int port;

    private final TestRestTemplate restTemplate = new TestRestTemplate();

    @Test
    void healthCheckEndpoint() {
        String url = "http://localhost:" + port + "/api/analysis/history";
        ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
        
        // Should return 200 even if no analyses exist
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
    }

    @Test
    void analyzeEndpointReturns500WhenDownstreamUnavailable() {
        String url = "http://localhost:" + port + "/api/analyze";
        String requestBody = """
            {
                "query": "test query",
                "mode": "auto"
            }
            """;
        
        ResponseEntity<String> response = restTemplate.postForEntity(url, requestBody, String.class);
        
        // Expect 500 because downstream services aren't running
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
    }
} 