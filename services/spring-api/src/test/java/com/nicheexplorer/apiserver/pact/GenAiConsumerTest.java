package com.nicheexplorer.apiserver.pact;

import au.com.dius.pact.consumer.MockServer;
import au.com.dius.pact.consumer.dsl.PactDslWithProvider;
import au.com.dius.pact.consumer.junit5.PactConsumerTestExt;
import au.com.dius.pact.consumer.junit5.PactTestFor;
import au.com.dius.pact.core.model.V4Pact;
import au.com.dius.pact.core.model.annotations.Pact;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nicheexplorer.generated.model.ClassifyRequest;
import com.nicheexplorer.generated.model.ClassifyResponse;
import com.nicheexplorer.generated.model.EmbeddingRequest;
import com.nicheexplorer.generated.model.EmbeddingResponse;
import com.nicheexplorer.generated.model.QueryBuilderRequest;
import com.nicheexplorer.generated.model.QueryBuilderResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.web.reactive.function.client.WebClient;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Pact consumer test for the contract between `api-server` and `py-genai`.
 *
 * Endpoints tested:
 * - POST /classify: Classifies a user query to determine the best data source.
 * - POST /embeddings: Generates embeddings for a list of texts.
 * - GET /embeddings: Retrieves cached embeddings by document IDs.
 * - POST /query/build/{source}: Builds a source-specific query.
 *
 * This test uses OpenAPI generated models to ensure schema compliance and
 * generates a pact file in `build/pacts/api-server-py-genai.json`
 * for the provider (`py-genai`) to verify.
 */
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "py-genai")
public class GenAiConsumerTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * Defines the contract for classifying a search query. It specifies the
     * expected request body and the successful response structure.
     */
    @Pact(consumer = "api-server", provider = "py-genai")
    public V4Pact classifyQueryPact(PactDslWithProvider builder) throws JsonProcessingException {
        var request = new ClassifyRequest().query("machine learning");
        var response = new ClassifyResponse()
                .source(ClassifyResponse.SourceEnum.ARXIV)
                .suggestedCategory("cs.AI");

        return builder
                .given("genai service is available for classification")
                .uponReceiving("a request to classify a query")
                .method("POST")
                .path("/classify")
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(request))
                .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(response))
                .toPact(V4Pact.class);
    }

    /**
     * Defines the contract for generating text embeddings. It specifies the
     * expected request body and the successful response structure.
     */
    @Pact(consumer = "api-server", provider = "py-genai")
    public V4Pact generateEmbeddingsPact(PactDslWithProvider builder) throws JsonProcessingException {
        var request = new EmbeddingRequest()
                .texts(List.of("text1", "text2"))
                .ids(List.of("id1", "id2"));
        var response = new EmbeddingResponse()
                .embeddings(List.of(
                        List.of(0.1f, 0.2f),
                        List.of(0.3f, 0.4f)
                ));

        return builder
                .given("genai service is available for embeddings")
                .uponReceiving("a request to generate embeddings")
                .method("POST")
                .path("/embeddings")
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(request))
                .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(response))
                .toPact(V4Pact.class);
    }

    /**
     * Defines the contract for retrieving cached text embeddings. It specifies
     * the expected response for a successful GET request.
     */
    @Pact(consumer = "api-server", provider = "py-genai")
    public V4Pact getEmbeddingsPact(PactDslWithProvider builder) throws JsonProcessingException {
        var response = new EmbeddingResponse()
                .embeddings(List.of(
                        List.of(0.5f, 0.6f),
                        List.of(0.7f, 0.8f)
                ));

        return builder
                .given("genai service has existing embeddings")
                .uponReceiving("a request to retrieve embeddings")
                .method("GET")
                .path("/embeddings")
                .query("ids=id1,id2")
                .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body(new ObjectMapper().writeValueAsString(response))
                .toPact(V4Pact.class);
    }

    /**
     * Defines the contract for building a source-specific query for arXiv.
     * It specifies the expected request body and the successful response structure.
     */
    @Pact(consumer = "api-server", provider = "py-genai")
    public V4Pact buildArxivQueryPact(PactDslWithProvider builder) throws JsonProcessingException {
        var request = new QueryBuilderRequest().searchTerms("machine learning");
        var response = new QueryBuilderResponse()
                .query("au:\"John Doe\" AND ti:\"Machine Learning\"")
                .description("Generated arXiv query")
                .source("arxiv");

        return builder
                .given("genai service is available for query building")
                .uponReceiving("a request to build an arxiv query")
                .method("POST")
                .path("/api/v1/query/build/arxiv")
                .body(new ObjectMapper().writeValueAsString(request))
                .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body(new ObjectMapper().writeValueAsString(response))
                .toPact(V4Pact.class);
    }

    @Test
    @PactTestFor(pactMethod = "classifyQueryPact")
    /**
     * Verifies that the `api-server` (Consumer) can correctly handle a response
     * from the `py-genai` (Provider) when requesting to classify a search query.
     *
     * Endpoint: POST /classify
     *
     * This is the very first step in an analysis. The
     * `api-server` sends the user's query to `py-genai` to decide which data
     * source is most appropriate. The entire workflow depends on this
     * classification being correct.
     */
    public void shouldClassifyQuery(MockServer mockServer) {
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();
        var request = new ClassifyRequest().query("machine learning");

        var response = webClient.post()
                .uri("/classify")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(ClassifyResponse.class)
                .block();

        assertThat(response).isNotNull();
        assertThat(response.getSource()).isEqualTo(ClassifyResponse.SourceEnum.ARXIV);
        assertThat(response.getSuggestedCategory()).isEqualTo("cs.AI");
    }

    @Test
    @PactTestFor(pactMethod = "generateEmbeddingsPact")
    /**
     * Verifies that the `api-server` (Consumer) can correctly handle a response
     * from the `py-genai` (Provider) when requesting to generate text embeddings.
     *
     * Endpoint: POST /embeddings
     *
     * After fetching articles, `api-server` needs to turn
     * their text into numerical vectors (embeddings) to find topics. It
     * delegates this task to `py-genai`. This test ensures the data exchange
     * for this core operation is reliable.
     */
    public void shouldGenerateEmbeddings(MockServer mockServer) {
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();
        var request = new EmbeddingRequest()
                .texts(List.of("text1", "text2"))
                .ids(List.of("id1", "id2"));

        var response = webClient.post()
                .uri("/embeddings")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(EmbeddingResponse.class)
                .block();

        assertThat(response).isNotNull();
        assertThat(response.getEmbeddings()).hasSize(2);
        assertThat(response.getEmbeddings().get(0)).containsExactly(0.1f, 0.2f);
        assertThat(response.getEmbeddings().get(1).get(1)).isEqualTo(0.4f);
    }

    @Test
    @PactTestFor(pactMethod = "getEmbeddingsPact")
    /**
     * Verifies that the `api-server` (Consumer) can correctly handle a response
     * from the `py-genai` (Provider) when requesting to retrieve cached text
     * embeddings.
     *
     * Endpoint: GET /embeddings
     *
     * This is an optimization. To avoid expensive
     * re-computation, `py-genai` caches embeddings. This test verifies that
     * `api-server` can retrieve these cached embeddings by their IDs, making
     * the analysis process faster.
     */
    public void shouldGetEmbeddings(MockServer mockServer) {
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();

        var response = webClient.get()
                .uri(uriBuilder -> uriBuilder.path("/embeddings").queryParam("ids", "id1,id2").build())
                .retrieve()
                .bodyToMono(EmbeddingResponse.class)
                .block();

        assertThat(response).isNotNull();
        assertThat(response.getEmbeddings()).hasSize(2);
        assertThat(response.getEmbeddings().get(0)).hasSize(2);
    }

    @Test
    @PactTestFor(pactMethod = "buildArxivQueryPact")
    /**
     * Verifies that the `api-server` (Consumer) can correctly handle a response
     * from the `py-genai` (Provider) when requesting to build a source-specific
     * query.
     *
     * Endpoint: POST /api/v1/query/build/{source}
     *
     * This tests an AI-powered feature where `py-genai`
     * can convert a simple user query into a complex, optimized query for a
     * specific source like arXiv. This test ensures the `api-server` can use
     * this query-building feature correctly.
     */
    public void shouldBuildArxivQuery(MockServer mockServer) {
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();

        var request = new QueryBuilderRequest().searchTerms("machine learning");

        var response = webClient.post()
                .uri("/api/v1/query/build/arxiv")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(QueryBuilderResponse.class)
                .block();

        assertThat(response).isNotNull();
        assertThat(response.getSource()).isEqualTo("arxiv");
        assertThat(response.getQuery()).isNotEmpty();
    }
} 