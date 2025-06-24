import logging
import numpy as np
from typing import List, Dict, Any
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from .arxiv_service import arxiv_service
from .embedding_service import embedding_service

logger = logging.getLogger(__name__)

class TopicDiscoveryService:
    def extract_topics(self, feed_url: str, max_articles: int = 50, min_frequency: int = 2) -> Dict[str, Any]:
        """
        Extracts topics from a feed of articles by fetching articles, getting their
        embeddings (from cache or by generation), clustering them, and deriving
        topic titles using TF-IDF.
        """
        logger.info(f"Starting topic discovery for feed: {feed_url} with max_articles={max_articles}")
        
        articles = arxiv_service.fetch_articles(feed_url, max_articles=max_articles)
        if not articles:
            return {"topics": [], "articles_processed": 0}

        # Delegate to EmbeddingService to get all embeddings (cached or new)
        embeddings_map = embedding_service.get_embeddings(articles)
        
        # We need to ensure the articles and embeddings are in the same order for clustering
        ordered_articles = []
        ordered_embeddings = []
        for article in articles:
            article_id = article.get_short_id()
            if article_id in embeddings_map:
                ordered_articles.append(article)
                ordered_embeddings.append(embeddings_map[article_id])

        if not ordered_embeddings:
            logger.warning("No embeddings were available for clustering.")
            return {"topics": [], "articles_processed": len(articles)}
            
        # Determine the optimal number of clusters
        num_clusters = self._calculate_optimal_clusters(len(ordered_articles))
        if num_clusters == 0:
            logger.warning("Not enough articles to form clusters.")
            return {"topics": [], "articles_processed": len(articles)}

        # Perform KMeans clustering
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(np.array(ordered_embeddings))
        
        # Group articles by their assigned cluster
        clustered_articles = {i: [] for i in range(num_clusters)}
        for i, article in enumerate(ordered_articles):
            clustered_articles[clusters[i]].append(article)
            
        # Generate topic titles and descriptions
        topic_titles = self._get_topic_titles(clustered_articles)
        
        # Format the final response
        topics_response = []
        for i, articles_in_cluster in clustered_articles.items():
            if len(articles_in_cluster) >= min_frequency:
                topic_id = f"topic_{i}"
                title = topic_titles.get(i, f"Topic {i+1}")
                
                formatted_articles = [{
                    "title": article.title,
                    "link": str(article.links[0]),
                    "abstract": article.summary
                } for article in articles_in_cluster]

                topics_response.append({
                    "id": topic_id,
                    "title": title,
                    "description": f"A cluster of {len(articles_in_cluster)} articles about {title}.",
                    "article_count": len(articles_in_cluster),
                    "relevance": 100,
                    "articles": formatted_articles
                })

        # Sort topics by the number of articles
        topics_response.sort(key=lambda x: x['article_count'], reverse=True)
        
        return {"topics": topics_response, "articles_processed": len(articles)}

    def _calculate_optimal_clusters(self, num_articles: int) -> int:
        """Dynamically calculates the number of clusters."""
        if num_articles < 4:
            return 0
        return max(2, min(10, num_articles // 4))

    def _get_topic_titles(self, clustered_articles: Dict[int, List[Any]]) -> Dict[int, str]:
        """Generates a single-word title for each cluster using TF-IDF."""
        topic_titles = {}
        for i, articles in clustered_articles.items():
            if not articles:
                continue
            
            corpus = [" ".join([a.title, a.summary]) for a in articles]
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1)
            
            try:
                tfidf_matrix = vectorizer.fit_transform(corpus)
                feature_names = vectorizer.get_feature_names_out()
                if feature_names.any():
                    # Use the single most important word as the title
                    topic_titles[i] = feature_names[0].capitalize()
                else:
                    topic_titles[i] = "Misc"
            except ValueError:
                # Handle cases where vocabulary is empty
                topic_titles[i] = "Misc"
                
        return topic_titles

# Singleton instance
topic_discovery_service = TopicDiscoveryService() 