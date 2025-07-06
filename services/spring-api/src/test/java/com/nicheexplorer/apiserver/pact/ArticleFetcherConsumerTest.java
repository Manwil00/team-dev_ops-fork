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
    /**
     * Defines the contract for fetching articles from arXiv. It specifies the
     * expected request body and the successful response structure.
     */
    @Pact(consumer = "api-server", provider = "py-fetcher")
    public V4Pact arxivArticlesFetch(PactDslWithProvider builder) throws JsonProcessingException {
        var request = new ArticleFetchRequest()
                .query("machine learning")
                .source(ArticleFetchRequest.SourceEnum.ARXIV)
                .limit(10)
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

        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());

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
     * Endpoint: POST /api/v1/articles
     *
     * After a query is classified, the `api-server` needs to fetch relevant
     * articles from `py-fetcher`. This test guarantees that the `api-server`
     * can correctly ask for articles and process the list it gets back.
     */
    public void shouldFetchArxivArticles(MockServer mockServer) {
        // Arrange
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();

        var request = new ArticleFetchRequest()
                .query("machine learning")
                .source(ArticleFetchRequest.SourceEnum.ARXIV)
                .limit(10)
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
     * successful response from the `py-fetcher` (Provider) when fetching the
     * available categories for a data source.
     *
     * Endpoint: GET /api/v1/sources/{source}/categories
     *
     * Display a list of available categories for a source like arXiv. The
     * `api-server` gets this information from `py-fetcher`. This test ensures
     * the `api-server` can fetch and understand this list of categories.
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
} 