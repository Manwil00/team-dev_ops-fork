import numpy as np
from typing import List, Dict, Any
import uuid
from sklearn.feature_extraction.text import TfidfVectorizer
import hdbscan
import umap
import re
from collections import Counter
from niche_explorer_models.models.embedding_request import EmbeddingRequest
from niche_explorer_models.models.embedding_response import EmbeddingResponse
from niche_explorer_models.models.topic_discovery_response import TopicDiscoveryResponse
from niche_explorer_models.models.topic import Topic
import logging
import os
import httpx
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------------
# TopicDiscoveryService – enhanced with advanced clustering and topic naming logic.
# ------------------------------------------------------------------------------------

class TopicDiscoveryService:
    def __init__(self, genai_base_url: str):
        self.genai_base_url = genai_base_url
        self.logger = logging.getLogger(__name__)

        # HTTP client session for GenAI embedding endpoints
        self.http_client: httpx.AsyncClient | None = None

    async def discover_topic(self, query: str, article_keys: list, articles: list,
                              min_cluster_size: int = 3, n_components: int = 15):
        """Discover topics by clustering article texts with TF-IDF → UMAP → HDBSCAN."""
        self.logger.info(
            f"Starting topic discovery for query: {query} (articles={len(articles)})"
        )

        if not articles:
            self.logger.warning("No articles provided – returning empty topic list")
            return TopicDiscoveryResponse(query=query, topics=[], total_articles_processed=0)

        try:
            # ------------------------------------------------------------------
            # 1) Retrieve embeddings from GenAI – fallback to TF-IDF if unavailable
            # ------------------------------------------------------------------
            embeddings: list[list[float]] = [None] * len(articles)

            # ------------------------------------------------------------------
            # 1. Try GET /embeddings?ids=...
            # ------------------------------------------------------------------
            try:
                if not self.http_client:
                    self.http_client = httpx.AsyncClient(timeout=30.0)

                resp = await self.http_client.get(
                    f"{self.genai_base_url.rstrip('/')}/api/v1/embeddings",
                    params={"ids": article_keys},
                )
                resp.raise_for_status()
                data = resp.json()
                returned_embeddings = data.get("embeddings", [])
                for idx, emb in enumerate(returned_embeddings):
                    if emb and len(emb) > 0:
                        embeddings[idx] = emb
            except Exception as e:
                self.logger.error("GET /embeddings failed: %s", e)

            # ------------------------------------------------------------------
            # 2. For missing ones call POST /embeddings
            # ------------------------------------------------------------------
            missing_indices = [i for i, emb in enumerate(embeddings) if emb is None]
            if missing_indices:
                texts_to_embed = [
                    f"{articles[i].title} {articles[i].summary or ''}".strip()
                    for i in missing_indices
                ]
                ids_to_embed = [article_keys[i] for i in missing_indices]

                try:
                    req_model = EmbeddingRequest(texts=texts_to_embed, ids=ids_to_embed)
                    resp = await self.http_client.post(
                        f"{self.genai_base_url.rstrip('/')}/api/v1/embeddings",
                        json=req_model.model_dump(by_alias=True),
                    )
                    resp.raise_for_status()
                    new_embeddings = resp.json().get("embeddings", [])
                    for idx, emb in zip(missing_indices, new_embeddings):
                        embeddings[idx] = emb
                except Exception as e:
                    self.logger.error("POST /embeddings failed: %s", e)

            # Final safety: replace any still-missing with zero-vector
            if any(e is None for e in embeddings):
                self.logger.warning("Some embeddings still missing – zero-vector fallback applied")
                # Determine dim
                try:
                    vector_len = len(next(e for e in embeddings if e is not None))
                except StopIteration:
                    vector_len = 768
                embeddings = [e if e is not None else [0.0] * vector_len for e in embeddings]

            # Now reduce dimensionality if embeddings are high-dimensional (>100)
            embeddings_array = np.array(embeddings, dtype=float)

            if embeddings_array.ndim != 2:
                embeddings_array = np.vstack(embeddings_array)

            embeddings_array = embeddings_array.astype(float)

            n_samples = len(articles)
            if n_samples < 5:
                reduced_embeddings = embeddings_array  # Skip dimensionality reduction for tiny datasets
            else:
                try:
                    if embeddings_array.shape[1] > 100:
                        reducer = umap.UMAP(n_components=50, metric="cosine", random_state=42)
                        reduced_embeddings = reducer.fit_transform(embeddings_array)
                    else:
                        # Use adaptive n_components but ensure < n_samples
                        n_comp = min( min(embeddings_array.shape[1], 15), n_samples - 1)
                        reducer = umap.UMAP(n_components=n_comp, metric="cosine", random_state=42)
                        reduced_embeddings = reducer.fit_transform(embeddings_array)
                except Exception as e:
                    self.logger.warning("UMAP failed (%s) – falling back to raw embeddings", e)
                    reduced_embeddings = embeddings_array

            # ------------------------------------------------------------------
            # 4) Clustering step (enhanced parameters)
            # ------------------------------------------------------------------
            if len(articles) <= 100:
                # Fast path – KMeans as before
                k = max(1, int(np.sqrt(len(articles) / 2)))
                self.logger.debug(f"Using fast KMeans clustering (k={k}) for {len(articles)} docs")
                cluster_labels = KMeans(n_clusters=k, random_state=42, n_init="auto").fit_predict(
                    reduced_embeddings)
                probabilities = np.ones(len(cluster_labels))  # KMeans has no prob; treat uniform
            else:
                effective_min_size = max(2, min(min_cluster_size, len(articles) // 8))
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=effective_min_size,
                    min_samples=max(1, effective_min_size - 1),
                    metric="euclidean",
                    cluster_selection_epsilon=0.05,
                    alpha=1.0,
                    cluster_selection_method="eom",
                )
                cluster_labels = clusterer.fit_predict(reduced_embeddings)
                probabilities = clusterer.probabilities_

            # Build clusters with confidences
            clusters: dict[int, dict[str, Any]] = {}
            for art, lbl, prob in zip(articles, cluster_labels, probabilities):
                if lbl == -1:
                    continue  # noise
                cluster = clusters.setdefault(lbl, {"articles": [], "conf": []})
                cluster["articles"].append(art)
                cluster["conf"].append(float(prob))

            self.logger.info("HDBSCAN yielded %d clusters from %d articles", len(clusters), len(articles))

            topics: list[Topic] = []

            if not clusters:
                # No clusters – fallback single topic
                topics.append(
                Topic(
                        id=str(uuid.uuid4()),
                        title=f"Main Topic: {query}",
                    description=f"Articles related to {query}",
                        article_count=len(articles),
                        relevance=100,
                        articles=articles[: min(len(articles), 50)],
                    )
                )
            else:
                total_articles = len(articles)
                for lbl, data in clusters.items():
                    cluster_articles = data["articles"]
                    avg_conf = sum(data["conf"]) / len(data["conf"]) if data["conf"] else 0.0

                    title_desc = self._generate_topic_info(cluster_articles)

                    topics.append(
                        Topic(
                            id=str(uuid.uuid4()),
                            title=title_desc["title"],
                            description=title_desc["description"],
                            article_count=len(cluster_articles),
                            relevance=int(avg_conf * 100),
                            articles=cluster_articles[: min(len(cluster_articles), 50)],
                        )
                    )

            # Sort topics
            topics = self._deduplicate_and_merge_topics(topics, min_cluster_size)
            # Resort after merge
            topics.sort(key=lambda t: (t.relevance, t.article_count), reverse=True)
            
            return TopicDiscoveryResponse(
                query=query,
                topics=topics,
                total_articles_processed=len(articles),
            )
            
        except Exception as e:
            self.logger.error(f"Error in topic discovery: {e}")
            return TopicDiscoveryResponse(
                query=query,
                topics=[],
                total_articles_processed=0,
            )

    def _cluster_and_label(self, embeddings, texts, min_cluster_size=3):
        """Advanced clustering and topic labeling with HDBSCAN and UMAP"""
        try:
            # Dimensionality reduction with UMAP
            reducer = umap.UMAP(n_components=50, random_state=42, metric='cosine')
            reduced_embeddings = reducer.fit_transform(embeddings)
            
            # Clustering with HDBSCAN
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                metric='euclidean',
                cluster_selection_method='eom'
            )
            cluster_labels = clusterer.fit_predict(reduced_embeddings)
            
            # Generate topic names and summaries
            topics = []
            unique_labels = set(cluster_labels)
            for label in unique_labels:
                if label == -1:  # Skip noise cluster
                    continue
                    
                cluster_texts = [texts[i] for i in range(len(texts)) if cluster_labels[i] == label]
                cluster_embeddings = [embeddings[i] for i in range(len(embeddings)) if cluster_labels[i] == label]
                
                topic_name = self._generate_topic_name(cluster_texts)
                topic_summary = self._generate_topic_summary(cluster_texts)
                
                topics.append({
                    'name': topic_name,
                    'summary': topic_summary,
                    'size': len(cluster_texts),
                    'texts': cluster_texts,
                    'embeddings': cluster_embeddings
                })
                
            return topics
            
        except Exception as e:
            self.logger.error(f"Clustering failed: {e}")
            return []

    def _generate_topic_name(self, texts):
        """Generate meaningful topic names using TF-IDF and pattern recognition"""
        try:
            if not texts:
                return "Unnamed Topic"
                
            # Combine all texts for analysis
            combined_text = " ".join(texts)
            
            # Extract technical terms (words with capitals, numbers, or common ML patterns)
            tech_terms = re.findall(r'\b[A-Z][a-z]*(?:[A-Z][a-z]*)*\b|\b\w*(?:ML|AI|CNN|RNN|LSTM|GAN|BERT)\w*\b', combined_text)
            
            # Use TF-IDF to find most important terms
            vectorizer = TfidfVectorizer(max_features=20, stop_words='english', ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.sum(axis=0).A1
            
            # Get top terms
            top_indices = scores.argsort()[-5:][::-1]
            top_terms = [feature_names[i] for i in top_indices]
            
            # Prefer technical terms if available
            if tech_terms:
                most_common_tech = Counter(tech_terms).most_common(3)
                name_parts = [term for term, _ in most_common_tech]
            else:
                name_parts = top_terms[:3]
                
            # Create readable topic name
            if len(name_parts) >= 2:
                return f"{name_parts[0]} & {name_parts[1]}"
            elif name_parts:
                return name_parts[0]
            else:
                return "Mixed Topics"
                
        except Exception as e:
            self.logger.error(f"Topic name generation failed: {e}")
            return "Unnamed Topic"

    def _generate_topic_summary(self, texts):
        """Generate concise topic summaries from clustered texts"""
        try:
            if not texts:
                return "No description available"
                
            # Extract key phrases using simple frequency analysis
            combined = " ".join(texts)
            sentences = re.split(r'[.!?]+', combined)
            
            # Find sentences with high keyword density
            important_sentences = []
            for sentence in sentences[:10]:  # Limit to first 10 sentences
                if len(sentence.strip()) > 20:  # Minimum length
                    important_sentences.append(sentence.strip())
                    
            if important_sentences:
                return important_sentences[0]  # Return first meaningful sentence
            else:
                return "Collection of related research articles"
                
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return "No description available"

    # ------------------------------------------------------------------
    # Advanced topic naming helpers (adapted from provided logic)
    # ------------------------------------------------------------------

    def _generate_topic_info(self, articles: List[Any]) -> Dict[str, str]:
        """Generate title/description using title keyphrases, TF-IDF & technical term heuristics."""
        if not articles:
            return {"title": "Unknown Topic", "description": "No articles available"}

        titles = [a.title for a in articles]
        texts = [f"{a.title} {a.summary or ''}" for a in articles]

        keyphrases = self._extract_keyphrases_from_titles(titles)
        technical_terms = self._extract_technical_terms(texts)
        tfidf_phrases = self._extract_tfidf_phrases(texts)

        candidates = keyphrases + technical_terms + tfidf_phrases
        if candidates:
            best = Counter(candidates).most_common(1)[0][0]
            title = self._clean_topic_title(best)
            description = self._generate_description(len(articles), technical_terms[:3])
            return {"title": title, "description": description}

        # Fallback
        return self._fallback_topic_generation(len(articles))

    def _extract_keyphrases_from_titles(self, titles: List[str]) -> List[str]:
        phrases: list[str] = []
        for title in titles:
            clean = re.sub(r"[^\w\s-]", " ", title.lower())
            clean = re.sub(r"\s+", " ", clean).strip()
            words = clean.split()
            for i in range(len(words) - 1):
                bi = " ".join(words[i:i+2])
                if self._is_meaningful_phrase(bi):
                    phrases.append(bi)
                if i < len(words) - 2:
                    tri = " ".join(words[i:i+3])
                    if self._is_meaningful_phrase(tri):
                        phrases.append(tri)
        return phrases

    def _extract_technical_terms(self, texts: List[str]) -> List[str]:
        patterns = [
            r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
            r"\b\w+(?:\s+\w+)*\s+(?:network|model|algorithm|method|approach|framework|system)\b",
            r"\b(?:deep|machine|reinforcement|supervised|unsupervised)\s+learning\b",
            r"\b(?:neural|convolutional|recurrent|transformer)\s+\w+\b",
            r"\b\w+(?:\s+\w+)*\s+(?:detection|recognition|segmentation|classification|prediction)\b",
        ]
        combined = " ".join(texts).lower()
        terms: list[str] = []
        for pat in patterns:
            terms += [m.lower().strip() for m in re.findall(pat, combined, re.IGNORECASE) if self._is_meaningful_phrase(m)]
        return list(set(terms))

    def _extract_tfidf_phrases(self, texts: List[str]) -> List[str]:
        try:
            vect = TfidfVectorizer(stop_words="english", max_features=50, ngram_range=(2, 3), min_df=1, max_df=0.8)
            mat = vect.fit_transform(texts)
            scores = np.asarray(mat.mean(axis=0)).flatten()
            idxs = scores.argsort()[-10:][::-1]
            feats = vect.get_feature_names_out()
            return [feats[i] for i in idxs if scores[i] > 0 and self._is_meaningful_phrase(feats[i])]
        except Exception as e:
            self.logger.debug("TF-IDF extraction failed: %s", e)
            return []

    def _is_meaningful_phrase(self, phrase: str) -> bool:
        stop_terms = {"the","and","or","but","in","on","at","to","for","of","with","by",
                      "this","that","these","those","is","are","was","were","be","been","have",
                      "has","had","do","does","did","will","would","could","should","paper","study",
                      "work","research","approach","method","result","results","analysis","evaluation",
                      "experiment","experiments","performance","based","using","used","propose","proposed",
                      "present","presented","show","shows"}
        words = phrase.strip().lower().split()
        if len(words) == 0 or all(w in stop_terms for w in words):
            return False
        return any(len(w) > 2 and w not in stop_terms for w in words)

    def _clean_topic_title(self, title: str) -> str:
        title = re.sub(r"[^\w\s-]", " ", title)
        title = re.sub(r"\s+", " ", title).strip()
        title = " ".join(w.capitalize() if len(w) > 1 else w for w in title.split())
        return title[:47] + "..." if len(title) > 50 else title

    def _generate_description(self, count: int, key_terms: List[str]) -> str:
        if key_terms:
            return f"Research cluster focusing on {', '.join(key_terms[:2])} ({count} papers)"
        return f"Research cluster with {count} related papers"

    def _fallback_topic_generation(self, count: int) -> Dict[str, str]:
        return {"title": f"Research Cluster {count}", "description": f"Collection of {count} related papers"}

    # ------------------------------------------------------------------
    # Post-processing utils
    # ------------------------------------------------------------------

    def _deduplicate_and_merge_topics(self, topics: List[Topic], min_cluster_size: int) -> List[Topic]:
        """Merge topics that have effectively the same cleaned title and re-attach
        very small clusters (size < min_cluster_size) to the nearest larger one.
        """

        # 1. Title-based deduplication
        merged: dict[str, Topic] = {}
        for t in topics:
            key = self._clean_topic_title(t.title).lower()
            existing = merged.get(key)
            if existing:
                # Merge articles, counts, keep highest relevance
                existing.articles.extend(t.articles)
                existing.article_count = len(existing.articles)
                existing.relevance = max(existing.relevance, t.relevance)
            else:
                merged[key] = t

        deduped = list(merged.values())

        # 2. Handle very small clusters ( < min_cluster_size )
        small = [t for t in deduped if t.article_count < max(2, min_cluster_size)]
        large = [t for t in deduped if t.article_count >= max(2, min_cluster_size)]

        if large and small:
            primary = max(large, key=lambda x: x.article_count)
            for s in small:
                primary.articles.extend(s.articles)
                primary.article_count = len(primary.articles)
                primary.relevance = max(primary.relevance, s.relevance)
            deduped = [t for t in large if t is not primary] + [primary]

        return deduped

# Global instance
genai_base_url = os.getenv("GENAI_BASE_URL", "http://genai:8000")
topic_service = TopicDiscoveryService(genai_base_url)
