package com.nicheexplorer.apiserver.pact;

import au.com.dius.pact.consumer.MockServer;
import au.com.dius.pact.consumer.dsl.DslPart;
import au.com.dius.pact.consumer.dsl.PactDslJsonBody;
import au.com.dius.pact.consumer.dsl.PactDslWithProvider;
import au.com.dius.pact.consumer.junit5.PactConsumerTestExt;
import au.com.dius.pact.consumer.junit5.PactTestFor;
import au.com.dius.pact.core.model.V4Pact;
import au.com.dius.pact.core.model.annotations.Pact;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.nicheexplorer.generated.model.Article;
import com.nicheexplorer.generated.model.ArticleFetchRequest;
import com.nicheexplorer.generated.model.ArticleFetchResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClient;

import java.net.URI;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Pact consumer test for the contract between `api-server` and `py-fetcher`.
 *
 * Endpoints tested:
 * - POST /api/v1/articles: Fetch articles from a specified source.
 * - GET /api/v1/sources/{source}/categories: Get available categories for a data source.
 *
 * This test uses OpenAPI generated models to ensure schema compliance and
 * generates a pact file in `build/pacts/api-server-py-fetcher.json`
 * for the provider (`py-fetcher`) to verify.
 */
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "py-fetcher")
public class ArticleFetcherConsumerTest {
    private final ObjectMapper objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule());

    /**
     * Defines the contract for fetching articles from arXiv. It specifies the
     * expected request body and the successful response structure.
     */
    @Pact(consumer = "api-server", provider = "py-fetcher")
    public V4Pact arxivArticlesFetch(PactDslWithProvider builder) throws JsonProcessingException {
        var request = new ArticleFetchRequest()
                .query("machine learning")
                .source(ArticleFetchRequest.SourceEnum.ARXIV)
                .limit(1)
                .category("cs.AI")
                .filters(Map.of());

        var article = new Article()
                .id("2301.00001")
                .title("Advanced Machine Learning Techniques")
                .link(URI.create("https://arxiv.org/abs/2301.00001"))
                .summary("This paper explores advanced ML techniques...")
                .authors(List.of("John Doe", "Jane Smith"))
                .published(OffsetDateTime.parse("2023-01-01T12:00:00Z"))
                .source(Article.SourceEnum.ARXIV)
                .metadata(Map.of());

        var response = new ArticleFetchResponse()
                .articles(List.of(article))
                .totalFound(1)
                .source(ArticleFetchResponse.SourceEnum.ARXIV);

        return builder
                .given("arxiv service is available")
                .uponReceiving("a request for machine learning articles")
                .method("POST")
                .path("/api/v1/articles")
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(request))
                .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(response))
                .toPact(V4Pact.class);
    }

    @Test
    @PactTestFor(pactMethod = "arxivArticlesFetch")
    /**
     * Verifies that the `api-server` (Consumer) can correctly process a
     * successful response from the `py-fetcher` (Provider) when fetching
     * articles.
     *
     * Test Description:
     * This test simulates the `api-server` making a valid request to fetch articles
     * from `py-fetcher`. It then asserts that the response is correctly deserialized.
     *
     * Assertions:
     * - `response` is not null, confirming a response was received.
     * - The list of `articles` has the expected size (1).
     * - The `source` of the first article is `ARXIV`, as expected.
     */
    public void shouldFetchArxivArticles(MockServer mockServer) {
        // Arrange
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();

        var request = new ArticleFetchRequest()
                .query("machine learning")
                .source(ArticleFetchRequest.SourceEnum.ARXIV)
                .limit(1)
                .category("cs.AI");

        // Act
        var response = webClient.post()
                .uri("/api/v1/articles")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(ArticleFetchResponse.class)
                .block();

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getArticles()).hasSize(1);
        assertThat(response.getArticles().get(0).getSource()).isEqualTo(Article.SourceEnum.ARXIV);
    }

    /**
     * Defines the contract for fetching available categories from arXiv.
     * It specifies the expected response for a successful GET request.
     */
    @Pact(consumer = "api-server", provider = "py-fetcher")
    public V4Pact arxivCategoriesPact(PactDslWithProvider builder) {
        return builder
                .given("arxiv categories are available")
                .uponReceiving("a request for arxiv categories")
                .method("GET")
                .path("/api/v1/sources/arxiv/categories")
                .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body("{\"Computer Science\": [\"cs.AI\", \"cs.CL\"]}")
                .toPact(V4Pact.class);
    }

    @Test
    @PactTestFor(pactMethod = "arxivCategoriesPact")
    /**
     * Verifies that the `api-server` (Consumer) can correctly process a
     * successful response from the `py-fetcher` (Provider) when fetching
     * available categories for a data source.
     *
     * Test Description:
     * This test simulates the `api-server` making a GET request to fetch the list
     * of available categories for the `arxiv` source.
     *
     * Assertions:
     * - `response` is not null.
     * - The response map contains the key "Computer Science".
     * - The list associated with "Computer Science" contains the expected category codes.
     */
    public void shouldFetchArxivCategories(MockServer mockServer) {
        // Arrange
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();

        // Act
        var response = webClient.get()
                .uri("/api/v1/sources/arxiv/categories")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, List<String>>>() {})
                .block();

        // Assert
        assertThat(response).isNotNull();
        assertThat(response).containsKey("Computer Science");
        assertThat(response.get("Computer Science")).contains("cs.AI", "cs.CL");
    }

    /**
     * Defines a contract for when the article fetch request is invalid
     * (e.g., missing the source), expecting a 400 Bad Request response.
     */
    @Pact(consumer = "api-server", provider = "py-fetcher")
    public V4Pact fetchArticlesBadRequest(PactDslWithProvider builder) throws JsonProcessingException {
        // Create a request that is deliberately invalid (missing required 'source')
        String invalidRequest = "{\"query\": \"machine learning\"}";

        var error = new com.nicheexplorer.generated.model.Error()
                .code("INVALID_REQUEST")
                .message("Source is a required field");

        return builder
                .given("arxiv service receives an invalid article fetch request")
                .uponReceiving("a request for articles with a missing source")
                .method("POST")
                .path("/api/v1/articles")
                .headers(Map.of("Content-Type", "application/json"))
                .body(invalidRequest)
                .willRespondWith()
                .status(400)
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(error))
                .toPact(V4Pact.class);
    }

    @Test
    @PactTestFor(pactMethod = "fetchArticlesBadRequest")
    /**
     * Verifies that the `api-server` (Consumer) can correctly handle a 400 Bad
     * Request from `py-fetcher` (Provider) if the article fetch request is invalid.
     *
     * Test Description:
     * This test simulates the `api-server` sending a deliberately invalid request
     * (a JSON body missing the required `source` field) to `py-fetcher`. It uses
     * `exchangeToMono` to inspect the raw HTTP response.
     *
     * Assertions:
     * - The HTTP status code is `400`.
     * - The error response body can be deserialized into an `Error` object.
     * - The `code` field of the error object is `INVALID_REQUEST`.
     */
    public void shouldHandleInvalidArticleFetch(MockServer mockServer) {
        // Arrange
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();

        String invalidRequest = "{\"query\": \"machine learning\"}"; // Missing 'source'

        // Act & Assert
        var errorResponse = webClient.post()
                .uri("/api/v1/articles")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(invalidRequest)
                .exchangeToMono(response -> {
                    assertThat(response.statusCode().value()).isEqualTo(400);
                    return response.bodyToMono(com.nicheexplorer.generated.model.Error.class);
                })
                .block();

        assertThat(errorResponse).isNotNull();
        assertThat(errorResponse.getCode()).isEqualTo("INVALID_REQUEST");
    }
} 