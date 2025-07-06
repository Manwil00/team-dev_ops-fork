package com.nicheexplorer.apiserver.pact;

import au.com.dius.pact.consumer.MockServer;
import au.com.dius.pact.consumer.dsl.PactDslWithProvider;
import au.com.dius.pact.consumer.junit5.PactConsumerTestExt;
import au.com.dius.pact.consumer.junit5.PactTestFor;
import au.com.dius.pact.core.model.V4Pact;
import au.com.dius.pact.core.model.annotations.Pact;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.nicheexplorer.generated.model.Article;
import com.nicheexplorer.generated.model.Topic;
import com.nicheexplorer.generated.model.TopicDiscoveryRequest;
import com.nicheexplorer.generated.model.TopicDiscoveryResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.web.reactive.function.client.WebClient;

import java.net.URI;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Pact consumer test for the contract between `api-server` and `py-topics`.
 *
 * Endpoints tested:
 * - POST /api/v1/topics/discover: Discovers topics from a list of articles.
 *
 * This test uses OpenAPI generated models to ensure schema compliance and
 * generates a pact file in `build/pacts/api-server-py-topics.json`
 * for the provider (`py-topics`) to verify.
 */
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "py-topics")
public class TopicDiscoveryConsumerTest {

    private final ObjectMapper objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule());

    /**
     * Defines the contract for discovering topics from a list of articles.
     * It specifies the expected request body and the successful response structure.
     */
    @Pact(consumer = "api-server", provider = "py-topics")
    public V4Pact discoverTopicsPact(PactDslWithProvider builder) throws JsonProcessingException {
        var article = new Article()
                .id("2301.00001")
                .title("Advanced Machine Learning Techniques")
                .summary("This paper explores advanced ML techniques...")
                .link(URI.create("https://arxiv.org/abs/2301.00001"))
                .authors(List.of("John Doe", "Jane Smith"))
                .published(OffsetDateTime.parse("2023-01-01T12:00:00Z"))
                .source(Article.SourceEnum.ARXIV);

        var request = new TopicDiscoveryRequest()
                .query("machine learning")
                .articles(List.of(article))
                .articleIds(List.of(article.getId()));

        var topic = new Topic()
                .id(UUID.randomUUID().toString())
                .title("ML Techniques")
                .description("A summary of ML techniques.")
                .relevance(90)
                .articles(List.of(article));

        var response = new TopicDiscoveryResponse()
                .topics(List.of(topic));

        return builder
                .given("topic discovery service is available")
                .uponReceiving("a request to discover topics")
                .method("POST")
                .path("/api/v1/topics/discover")
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(request))
                .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body(objectMapper.writeValueAsString(response))
                .toPact(V4Pact.class);
    }

    @Test
    @PactTestFor(pactMethod = "discoverTopicsPact")
    /**
     * Verifies that the `api-server` (Consumer) can correctly process a
     * successful response from the `py-topics` (Provider) when requesting
     * topic discovery.
     *
     * Endpoint: POST /api/v1/topics/discover
     *
     * This is the final and most complex step in the
     * backend processing. The `api-server` sends the fetched articles and
     * their embeddings to the `py-topics` service for clustering. This test
     * is critical because it validates the contract for this large and
     * complex data exchange, ensuring the final results can be generated and
     * understood by the `api-server`.
     */
    public void shouldDiscoverTopics(MockServer mockServer) {
        var webClient = WebClient.builder()
                .baseUrl(mockServer.getUrl())
                .build();

        var article = new Article()
                .id("2301.00001")
                .title("Advanced Machine Learning Techniques")
                .summary("This paper explores advanced ML techniques...")
                .link(URI.create("https://arxiv.org/abs/2301.00001"))
                .authors(List.of("John Doe", "Jane Smith"))
                .published(OffsetDateTime.parse("2023-01-01T12:00:00Z"))
                .source(Article.SourceEnum.ARXIV);

        var request = new TopicDiscoveryRequest()
                .query("machine learning")
                .articles(List.of(article))
                .articleIds(List.of(article.getId()));

        var response = webClient.post()
                .uri("/api/v1/topics/discover")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(TopicDiscoveryResponse.class)
                .block();

        assertThat(response).isNotNull();
        assertThat(response.getTopics()).hasSize(1);
        Topic topic = response.getTopics().get(0);
        assertThat(topic.getTitle()).isEqualTo("ML Techniques");
        assertThat(topic.getArticles()).extracting(Article::getId).contains(article.getId());
    }
} 