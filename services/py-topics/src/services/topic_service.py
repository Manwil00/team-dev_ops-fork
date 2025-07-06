import numpy as np
from typing import List, Any
import uuid
from bertopic import BERTopic
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from niche_explorer_models.models.embedding_request import EmbeddingRequest
from niche_explorer_models.models.generate_text_request import GenerateTextRequest
from niche_explorer_models.models.topic_discovery_response import TopicDiscoveryResponse
from niche_explorer_models.models.topic import Topic
import logging
import os
import httpx
import re

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------------
# TopicDiscoveryService – now powered by the BERTopic library.
# ------------------------------------------------------------------------------------


class TopicDiscoveryService:
    def __init__(self, genai_base_url: str):
        self.genai_base_url = genai_base_url
        self.logger = logging.getLogger(__name__)
        self.http_client: httpx.AsyncClient | None = None

    async def discover_topic(
        self, query: str, article_keys: list, articles: list, min_cluster_size: int = 3
    ) -> TopicDiscoveryResponse:
        """Discover topics by clustering with BERTopic using external embeddings."""
        self.logger.info(f"Starting BERTopic discovery for {len(articles)} articles.")

        if not articles:
            return TopicDiscoveryResponse(
                query=query, topics=[], total_articles_processed=0
            )

        try:
            # 1. Fetch embeddings and filter out any articles for which it failed
            embeddings = await self._get_embeddings(article_keys, articles)
            valid_indices = [i for i, emb in enumerate(embeddings) if emb is not None]
            if not valid_indices:
                raise ValueError("Could not retrieve any embeddings.")

            final_articles = [articles[i] for i in valid_indices]
            embeddings_array = np.array(
                [embeddings[i] for i in valid_indices], dtype=float
            )
            docs = [
                f"{art.title} {art.summary or ''}".strip() for art in final_articles
            ]

            # 2. Run BERTopic, now with stop words removed for better quality topics
            vectorizer_model = CountVectorizer(stop_words="english")
            topic_model = BERTopic(
                min_topic_size=min_cluster_size,
                vectorizer_model=vectorizer_model,
                verbose=False,
            )
            topic_model.fit_transform(docs, embeddings_array)
            self.logger.info(
                f"BERTopic found {topic_model.get_topic_info()['Topic'].nunique() - 1} topics."
            )

            # 3. Process results using pandas for conciseness
            topics_df = topic_model.get_topic_info()
            # Filter out the outlier topic
            topics_df = topics_df[topics_df.Topic != -1]

            # Get the documents and their assigned topics
            documents_df = pd.DataFrame(
                {"doc": docs, "article": final_articles, "topic": topic_model.topics_}
            )

            # Group articles by topic
            articles_by_topic = (
                documents_df[documents_df.topic != -1]
                .groupby("topic")["article"]
                .apply(list)
            )

            # Generate a stable UUID for each topic ID
            topic_id_to_uuid = {
                topic_id: str(uuid.uuid4()) for topic_id in articles_by_topic.keys()
            }

            self.logger.info(
                f"Found {len(topics_df)} topics to process. Starting description generation."
            )
            response_topics = []
            for _, topic_row in topics_df.iterrows():
                topic_id = topic_row.Topic
                self.logger.info(f"Processing topic ID: {topic_id}")

                # Skip if the topic has no articles after filtering
                if topic_id not in topic_id_to_uuid:
                    continue

                new_topic_id = topic_id_to_uuid[topic_id]
                topic_representation = topic_row.Representation
                title = self._clean_topic_title(topic_row.Name)

                # Get articles for the current topic
                topic_articles = articles_by_topic.get(topic_id, [])

                # Generate a better description using the LLM service
                self.logger.info(
                    f"Generating description for topic {topic_id} ('{title}')..."
                )
                description = await self._generate_description_from_llm(
                    keywords=topic_representation,
                    documents=topic_articles[:4],  # Pass top 4 representative articles
                )
                self.logger.info(
                    f"Successfully generated description for topic {topic_id}."
                )

                response_topics.append(
                    Topic(
                        id=new_topic_id,
                        title=title,
                        description=description,
                        article_count=len(topic_articles),
                        relevance=int(topic_row.get("Relevance", 100)),
                        articles=topic_articles,
                    )
                )

            response_topics.sort(
                key=lambda t: (t.relevance, t.article_count), reverse=True
            )

            return TopicDiscoveryResponse(
                query=query,
                topics=response_topics,
                total_articles_processed=len(final_articles),
            )

        except Exception as e:
            self.logger.error(f"Error in BERTopic discovery: {e}", exc_info=True)
            return self._fallback_response(query, articles)

    async def _get_embeddings(
        self, article_keys: list, articles: list
    ) -> List[list[float] | None]:
        """Fetches embeddings from the GenAI service, with a GET->POST fallback."""
        embeddings: List[list[float] | None] = [None] * len(articles)
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)

        # Try GET first
        try:
            resp = await self.http_client.get(
                f"{self.genai_base_url.rstrip('/')}/api/v1/embeddings",
                params={"ids": article_keys},
            )
            resp.raise_for_status()
            for idx, emb in enumerate(resp.json().get("embeddings", [])):
                if emb:
                    embeddings[idx] = emb
        except Exception as e:
            self.logger.error("GET /embeddings failed: %s", e)

        # Fallback to POST for any missing embeddings
        missing_indices = [i for i, emb in enumerate(embeddings) if emb is None]
        if missing_indices:
            texts_to_embed = [
                f"{articles[i].title} {articles[i].summary or ''}".strip()
                for i in missing_indices
            ]
            ids_to_embed = [article_keys[i] for i in missing_indices]
            try:
                req = EmbeddingRequest(texts=texts_to_embed, ids=ids_to_embed)
                resp = await self.http_client.post(
                    f"{self.genai_base_url.rstrip('/')}/api/v1/embeddings",
                    json=req.model_dump(by_alias=True),
                )
                resp.raise_for_status()
                for idx, emb in zip(missing_indices, resp.json().get("embeddings", [])):
                    embeddings[idx] = emb
            except Exception as e:
                self.logger.error("POST /embeddings failed: %s", e)

        return embeddings

    def _fallback_response(self, query: str, articles: list) -> TopicDiscoveryResponse:
        """Returns a generic response if detailed topic modeling fails."""
        return TopicDiscoveryResponse(
            query=query,
            topics=[
                Topic(
                    id=str(uuid.uuid4()),
                    title=f"General Topic: {query}",
                    description="Could not perform detailed topic modeling.",
                    article_count=len(articles),
                    relevance=50,
                    articles=articles[:50],
                )
            ],
            total_articles_processed=len(articles),
        )

    def _clean_topic_title(self, title: str) -> str:
        """Removes the prefixed topic number and underscores from BERTopic names."""
        return re.sub(r"^\d+_", "", title).replace("_", " ").strip().capitalize()

    async def _generate_description_from_llm(
        self, keywords: List[str], documents: List[Any]
    ) -> str:
        """Generates a topic description using the GenAI service."""
        if not self.http_client:
            # Use a longer timeout for potentially slow LLM calls
            self.http_client = httpx.AsyncClient(timeout=60.0)

        if not documents:
            return f"A topic related to: {', '.join(keywords)}"

        # Format documents and keywords for the prompt, following the user's example
        doc_texts = [f"- {doc.title}: {doc.summary or ''}".strip() for doc in documents]
        doc_string = "\n".join(doc_texts)
        keyword_string = ", ".join(keywords)

        prompt = (
            "I have a topic that contains the following documents:\n[DOCUMENTS]\n\n"
            "The topic is described by the following keywords: [KEYWORDS]\n\n"
            "Based on the above information, please provide a concise, three-sentence summary that captures the essence of the topic. "
            "Do not just list the keywords or repeat the document titles. Synthesize the information into a coherent description."
        )

        # Replace placeholders
        final_prompt = prompt.replace("[DOCUMENTS]", doc_string).replace(
            "[KEYWORDS]", keyword_string
        )

        self.logger.debug(
            f"Generating description with prompt: {final_prompt[:300]}..."
        )
        try:
            req = GenerateTextRequest(prompt=final_prompt)
            resp = await self.http_client.post(
                f"{self.genai_base_url.rstrip('/')}/api/v1/generate/text",
                json=req.model_dump(by_alias=True),
            )
            resp.raise_for_status()
            # Assuming the response model is GenerateTextResponse
            generated_text = resp.json().get(
                "text", f"A topic related to: {keyword_string}"
            )
            self.logger.debug(f"LLM returned description: {generated_text[:100]}...")
            return generated_text
        except Exception as e:
            self.logger.error(f"Failed to generate topic description from LLM: {e}")
            return f"A topic related to: {keyword_string}"


# Initialize service instance for the main application to import
topic_service = TopicDiscoveryService(
    genai_base_url=os.getenv("GENAI_BASE_URL", "http://py-genai:8000")
)
