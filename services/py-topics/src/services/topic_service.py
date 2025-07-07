import asyncio
import numpy as np
from typing import List, Dict
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

# Prompts for the LLM
LABEL_PROMPT = "Your task is to create a concise, 5-word topic label. The topic is defined by these keywords: [KEYWORDS] and these documents: [DOCUMENTS]. Return ONLY the label itself, with no additional text or explanations."
DESCRIPTION_PROMPT = "Your task is to write a two-sentence summary for a topic. The topic is defined by these keywords: [KEYWORDS] and these documents: [DOCUMENTS]. Return ONLY the two-sentence summary, with no additional text or explanations."
# Combined prompt that requests both pieces in one go to reduce latency
COMBINED_PROMPT = (
    "You are given a topic described by these keywords: [KEYWORDS] and these documents: [DOCUMENTS]. "
    "Return a concise JSON object with exactly two keys: 'label' — a 5-word title, and 'description' — a two-sentence summary. "
    "Do NOT include any additional keys, formatting, markdown fences, or explanations."
)


class TopicDiscoveryService:
    def __init__(self, genai_base_url: str):
        self.genai_base_url = genai_base_url
        self.logger = logging.getLogger(__name__)
        self.http_client: httpx.AsyncClient | None = None

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=60.0)
        return self.http_client

    async def discover_topic(
        self,
        query: str,
        article_keys: list,
        articles: list,
        min_cluster_size: int = 2,
        nr_topics: int | None = 5,
        max_articles_per_topic: int = 40,
    ) -> TopicDiscoveryResponse:
        self.logger.info(f"Starting BERTopic discovery for {len(articles)} articles.")
        if not articles:
            return TopicDiscoveryResponse(
                query=query, topics=[], total_articles_processed=0
            )

        try:
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

            vectorizer_model = CountVectorizer(stop_words="english")
            topic_model = BERTopic(
                min_topic_size=min_cluster_size,
                vectorizer_model=vectorizer_model,
                verbose=False,
                nr_topics=nr_topics,
            )
            topic_model.fit_transform(docs, embeddings_array)

            topics_df = topic_model.get_topic_info()
            topics_df = topics_df[topics_df.Topic != -1]

            tasks = []
            for _, topic_row in topics_df.iterrows():
                tasks.append(
                    self._generate_representations_for_topic(
                        topic_model, topic_row.Topic, docs
                    )
                )

            generated_reps = await asyncio.gather(*tasks)
            rep_map = {rep["id"]: rep for rep in generated_reps if rep}

            documents_df = pd.DataFrame(
                {"doc": docs, "article": final_articles, "topic": topic_model.topics_}
            )
            articles_by_topic = (
                documents_df[documents_df.topic != -1]
                .groupby("topic")["article"]
                .apply(list)
            )
            topic_id_to_uuid = {
                topic_id: str(uuid.uuid4()) for topic_id in articles_by_topic.keys()
            }

            response_topics = []
            for _, topic_row in topics_df.iterrows():
                topic_id = topic_row.Topic
                if topic_id not in topic_id_to_uuid or topic_id not in rep_map:
                    continue

                new_topic_id = topic_id_to_uuid[topic_id]
                generated_rep = rep_map[topic_id]
                title = self._clean_topic_title(generated_rep["label"])
                description = generated_rep["description"]
                topic_articles = articles_by_topic.get(topic_id, [])
                relevance_score = (
                    int(round(100 * len(topic_articles) / len(final_articles)))
                    if final_articles
                    else 100
                )

                # ------------------------------------------------------------
                # Hierarchical sub-clustering: if a topic is still very large
                # (> 10 articles) try to split it into finer sub-topics using
                # a second BERTopic pass with smaller min_cluster_size.
                # ------------------------------------------------------------
                child_topics: list[Topic] = []
                if len(topic_articles) > 10:
                    child_docs = [
                        f"{art.title} {art.summary or ''}".strip()
                        for art in topic_articles
                    ]

                    try:
                        # Use the same embeddings for these docs (slice by index)
                        child_indices = [docs.index(d) for d in child_docs]
                        child_embs = embeddings_array[child_indices]

                        child_model = BERTopic(
                            min_topic_size=2, nr_topics=None, verbose=False
                        )
                        child_model.fit_transform(child_docs, child_embs)

                        child_info = child_model.get_topic_info()
                        child_info = child_info[child_info.Topic != -1]

                        # Map child topic id -> article list
                        child_mapping: dict[int, list] = {}
                        for idx, child_id in enumerate(child_model.topics_):
                            if child_id == -1:
                                continue
                            child_mapping.setdefault(child_id, []).append(
                                topic_articles[idx]
                            )

                        # Generate LLM-based representations for child topics
                        child_tasks = [
                            self._generate_representations_for_topic(
                                child_model, row.Topic, child_docs
                            )
                            for _, row in child_info.iterrows()
                        ]
                        child_reps = await asyncio.gather(*child_tasks)
                        child_rep_map = {rep["id"]: rep for rep in child_reps if rep}

                        for _, child_row in child_info.iterrows():
                            cid = child_row.Topic
                            rep = child_rep_map.get(cid)
                            c_articles = child_mapping.get(cid, [])

                            title_c = self._clean_topic_title(
                                rep["label"] if rep else child_row.Name
                            )
                            desc_c = (
                                rep["description"]
                                if rep
                                else f"Sub-topic within '{title}'"
                            )

                            rel_child = (
                                int(round(100 * len(c_articles) / len(final_articles)))
                                if final_articles
                                else 100
                            )
                            child_topics.append(
                                Topic(
                                    id=str(uuid.uuid4()),
                                    title=title_c,
                                    description=desc_c,
                                    article_count=len(c_articles),
                                    relevance=rel_child,
                                    articles=c_articles[:max_articles_per_topic],
                                )
                            )
                    except Exception as sub_e:
                        self.logger.warning("Sub-clustering failed: %s", sub_e)

                if child_topics:
                    response_topics.extend(child_topics)
                else:
                    response_topics.append(
                        Topic(
                            id=new_topic_id,
                            title=title,
                            description=description,
                            article_count=len(topic_articles),
                            relevance=relevance_score,
                            articles=topic_articles[:max_articles_per_topic],
                        )
                    )

            # Re-compute relevance relative to the largest topic so the winner is 100%
            if response_topics:
                max_size = max(t.article_count for t in response_topics)
                for t in response_topics:
                    t.relevance = (
                        int(round(100 * t.article_count / max_size))
                        if max_size
                        else 100
                    )

            response_topics.sort(
                key=lambda t: (t.relevance, t.article_count), reverse=True
            )

            # Cap number of topics if caller requested a limit
            if nr_topics is not None:
                response_topics = response_topics[:nr_topics]
            else:
                # Heuristic: keep at most 10 most relevant clusters to avoid overload
                if len(response_topics) > 10:
                    response_topics = response_topics[:10]

            return TopicDiscoveryResponse(
                query=query,
                topics=response_topics,
                total_articles_processed=len(final_articles),
            )

        except Exception as e:
            self.logger.error(f"Error in BERTopic discovery: {e}", exc_info=True)
            return self._fallback_response(query, articles)

    async def _generate_representations_for_topic(
        self, topic_model: BERTopic, topic_id: int, docs: List[str]
    ) -> Dict | None:
        try:
            keywords = topic_model.get_topic(topic_id)
            representative_docs = topic_model.get_representative_docs(topic_id)

            if not keywords or not representative_docs:
                self.logger.warning(
                    f"Could not retrieve keywords or docs for topic {topic_id}"
                )
                # Fallback to default representations
                return {
                    "id": topic_id,
                    "label": "Topic " + str(topic_id),
                    "description": "No description available.",
                }

            # Single LLM call requesting both label and description to cut latency
            combined_json = await self._generate_text_from_llm(
                COMBINED_PROMPT, keywords, representative_docs
            )

            import json as _json

            label = ""
            description = ""
            try:
                # Strip potential markdown fences or code blocks
                cleaned = combined_json.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.strip("` ")
                parsed = _json.loads(cleaned)
                label = parsed.get("label", "")
                description = parsed.get("description", "")
            except Exception as parse_e:
                self.logger.warning(
                    "Failed to parse combined LLM output for topic %s: %s",
                    topic_id,
                    parse_e,
                )
                label = combined_json[:50]  # fallback first 50 chars
                description = combined_json

            return {"id": topic_id, "label": label, "description": description}
        except Exception as e:
            self.logger.error(
                f"Failed to generate representation for topic {topic_id}: {e}"
            )
            return None

    async def _generate_text_from_llm(
        self, prompt_template: str, keywords: List[str], documents: List[str]
    ) -> str:
        client = await self._get_async_client()
        keyword_str = ", ".join([kw[0] for kw in keywords])
        doc_str = "\n".join([f"- {doc}" for doc in documents])
        final_prompt = prompt_template.replace("[KEYWORDS]", keyword_str).replace(
            "[DOCUMENTS]", doc_str
        )

        req = GenerateTextRequest(prompt=final_prompt)
        resp = await client.post(
            f"{self.genai_base_url.rstrip('/')}/api/v1/generate/text",
            json=req.model_dump(by_alias=True),
        )
        resp.raise_for_status()
        return resp.json().get("text", "")

    async def _get_embeddings(
        self, article_keys: list, articles: list
    ) -> List[list[float] | None]:
        client = await self._get_async_client()
        embeddings: List[list[float] | None] = [None] * len(articles)
        try:
            resp = await client.get(
                f"{self.genai_base_url.rstrip('/')}/api/v1/embeddings",
                params={"ids": article_keys},
            )
            resp.raise_for_status()
            for idx, emb in enumerate(resp.json().get("embeddings", [])):
                if emb:
                    embeddings[idx] = emb
        except Exception as e:
            self.logger.error("GET /embeddings failed: %s", e)

        missing_indices = [i for i, emb in enumerate(embeddings) if emb is None]
        if missing_indices:
            texts_to_embed = [
                f"{articles[i].title} {articles[i].summary or ''}".strip()
                for i in missing_indices
            ]
            ids_to_embed = [article_keys[i] for i in missing_indices]
            try:
                req = EmbeddingRequest(texts=texts_to_embed, ids=ids_to_embed)
                resp = await client.post(
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
        base_title = re.sub(r"^\d+_", "", title).replace("_", " ")
        base_title = re.sub(
            r"^(label|topic|name):?\s*\"?", "", base_title, flags=re.IGNORECASE
        ).strip()
        base_title = base_title.strip('"')
        return base_title.capitalize()


# Initialize service instance for the main application to import
topic_service = TopicDiscoveryService(
    genai_base_url=os.getenv("GENAI_BASE_URL", "http://py-genai:8000")
)
