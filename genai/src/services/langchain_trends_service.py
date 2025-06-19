"""
LangChain-based semantic topic discovery service using vector embeddings
and semantic clustering for intelligent trend identification.
"""

import feedparser
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import re
from sklearn.decomposition import PCA

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.embeddings import SentenceTransformerEmbeddings, HuggingFaceEmbeddings

# Alternative embedding options
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

logger = logging.getLogger(__name__)

class LangChainTrendsService:
    """
    Advanced semantic topic discovery using LangChain vector embeddings.
    
    This service:
    1. Converts RSS articles to vector embeddings using sentence-transformers
    2. Uses semantic clustering (DBSCAN) to discover topic groups
    3. Identifies trending topics based on cluster density and semantic similarity
    4. Generates human-readable topic titles using the most representative articles
    """
    
    def __init__(self, use_google_embeddings: bool = False):
        self.use_google_embeddings = use_google_embeddings and GOOGLE_AVAILABLE
        self.embeddings = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize embedding model - Google Gemini or Sentence Transformers"""
        try:
            if self.use_google_embeddings:
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001"
                )
                logger.info("Initialized Google Generative AI embeddings")
            else:
                # Use high-quality sentence transformer for semantic understanding
                self.embeddings = SentenceTransformerEmbeddings(
                    model_name="all-MiniLM-L6-v2"  # Fast, good quality embeddings
                )
                logger.info("Initialized SentenceTransformer embeddings")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            # Fallback to basic sentence transformers
            self.embeddings = SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )
    
    def extract_trending_topics(self, feed_url: str, max_articles: int = 50, 
                               min_frequency: int = 2) -> List[Dict[str, Any]]:
        """
        Extract trending topics using simplified keyword-based approach.
        This is a simplified version while debugging the semantic clustering.
        """
        
        # Step 1: Fetch articles
        logger.info(f"DEBUG: Starting extract_trending_topics with feed_url={feed_url}, max_articles={max_articles}, min_frequency={min_frequency}")
        articles = self._fetch_articles(feed_url, max_articles)
        logger.info(f"DEBUG: Fetched {len(articles)} articles")
        
        if len(articles) < 3:
            logger.info(f"DEBUG: Insufficient articles ({len(articles)}) for trend analysis")
            return []
        
        # Simplified approach: Create topics based on common keywords in titles
        topics = []
        
        # Group articles by common keywords
        keyword_groups = self._simple_keyword_grouping(articles)
        logger.info(f"DEBUG: Found {len(keyword_groups)} keyword groups")
        
        for i, (keyword, group_articles) in enumerate(keyword_groups.items()):
            if len(group_articles) >= min_frequency:
                # Prepare articles list (show all articles, no artificial cap)
                articles_list = [
                    {
                        'title': article.get('title', 'Untitled'),
                        'link': article.get('link', ''),
                        'abstract': article.get('summary', '') or article.get('description', '')
                    }
                    for article in group_articles  # Show all articles in the group
                ]
                
                topic = {
                    'id': f'topic_{i}_{hash(keyword) % 10000}',
                    'title': f"{keyword.title()} Research",
                    'description': f"Recent research advances in {keyword.lower()}",
                    'article_count': len(articles_list),  # Match the actual number of articles being returned
                    'relevance': min(100, 50 + min(len(articles_list) * 3, 50)),  # Scale relevance based on article count, capped at 100
                    'articles': articles_list
                }
                topics.append(topic)
        
        # Sort by relevance and return top topics
        topics.sort(key=lambda x: (x['relevance'], x['article_count']), reverse=True)
        logger.info(f"DEBUG: Created {len(topics)} topics")
        
        return topics[:6]  # Return top 6 topics
    
    def _simple_keyword_grouping(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Simple keyword-based grouping for testing"""
        keyword_groups = defaultdict(list)
        
        # Common ML/AI keywords to look for
        keywords = [
            'neural', 'deep', 'learning', 'network', 'vision', 'language', 
            'detection', 'classification', 'transformer', 'attention',
            'segmentation', 'generation', 'model', 'training', 'optimization'
        ]
        
        for article in articles:
            title = article.get('title', '').lower()
            summary = (article.get('summary', '') or article.get('description', '')).lower()
            full_text = f"{title} {summary}"
            
            # Find which keywords appear in this article
            article_keywords = []
            for keyword in keywords:
                if keyword in full_text:
                    article_keywords.append(keyword)
            
            # Add to the most relevant keyword group (or create new group)
            if article_keywords:
                # Use the first keyword found
                primary_keyword = article_keywords[0]
                keyword_groups[primary_keyword].append(article)
            else:
                # Fallback: extract first meaningful word from title
                title_words = re.findall(r'\b[a-zA-Z]{4,}\b', title)
                if title_words:
                    fallback_keyword = title_words[0].lower()
                    keyword_groups[fallback_keyword].append(article)
        
        return dict(keyword_groups)
    
    def _generate_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Generate vector embeddings for text documents"""
        try:
            # Use sync embedding generation (async not needed here)
            vectors = self.embeddings.embed_documents(texts)
            return np.array(vectors)
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None
    
    def _perform_semantic_clustering(self, embeddings: np.ndarray, 
                                   documents: List[Document]) -> Dict[int, List[int]]:
        """
        Perform semantic clustering using DBSCAN for density-based topic discovery.
        DBSCAN is ideal because:
        - Automatically determines number of clusters
        - Handles noise/outliers well  
        - Finds clusters of varying density
        """
        try:
            # Use DBSCAN for adaptive clustering
            # eps: maximum distance between points in same cluster
            # min_samples: minimum points to form a cluster
            clustering = DBSCAN(
                eps=0.3,  # Cosine distance threshold
                min_samples=max(2, len(documents) // 10),  # Adaptive min cluster size
                metric='cosine'
            )
            
            cluster_labels = clustering.fit_predict(embeddings)
            
            # Group documents by cluster
            clusters = defaultdict(list)
            for doc_idx, cluster_id in enumerate(cluster_labels):
                if cluster_id != -1:  # Ignore noise points
                    clusters[cluster_id].append(doc_idx)
            
            logger.info(f"Found {len(clusters)} semantic clusters from {len(documents)} documents")
            return dict(clusters)
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            # Fallback to KMeans with fixed number of clusters
            return self._fallback_kmeans_clustering(embeddings, documents)
    
    def _fallback_kmeans_clustering(self, embeddings: np.ndarray, 
                                  documents: List[Document]) -> Dict[int, List[int]]:
        """Fallback clustering using KMeans"""
        try:
            n_clusters = min(5, max(2, len(documents) // 8))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            clusters = defaultdict(list)
            for doc_idx, cluster_id in enumerate(cluster_labels):
                clusters[cluster_id].append(doc_idx)
            
            return dict(clusters)
        except Exception as e:
            logger.error(f"Fallback clustering failed: {e}")
            return {}
    
    def _generate_topics_from_clusters(self, clusters: Dict[int, List[int]], 
                                     documents: List[Document],
                                     article_metadata: List[Dict],
                                     embeddings: np.ndarray) -> List[Dict[str, Any]]:
        """Generate human-readable topics from semantic clusters"""
        topics = []
        
        for cluster_id, doc_indices in clusters.items():
            if len(doc_indices) < 2:  # Skip single-document clusters
                continue
            
            # Get cluster documents and their embeddings
            cluster_docs = [documents[i] for i in doc_indices]
            cluster_embeddings = embeddings[doc_indices]
            cluster_articles = [article_metadata[i] for i in doc_indices]
            
            # Find the most representative document (closest to cluster centroid)
            centroid = np.mean(cluster_embeddings, axis=0)
            similarities = cosine_similarity([centroid], cluster_embeddings)[0]
            most_representative_idx = np.argmax(similarities)
            representative_doc = cluster_docs[most_representative_idx]
            
            # Extract key terms and generate topic title
            topic_title = self._generate_topic_title(cluster_docs)
            topic_description = self._generate_topic_description(cluster_docs, topic_title)
            
            # Calculate cluster cohesion (average pairwise similarity)
            pairwise_similarities = cosine_similarity(cluster_embeddings)
            cohesion = np.mean(pairwise_similarities[np.triu_indices_from(pairwise_similarities, k=1)])
            
            # Calculate more sophisticated relevance score
            article_support_factor = min(1.0, len(cluster_articles) / 5.0)  # Bonus for larger clusters
            base_relevance = cohesion * 100
            final_relevance = int(base_relevance * (0.7 + 0.3 * article_support_factor))
            
            # Create topic
            topic = {
                'id': f"semantic_{cluster_id}_{hash(topic_title) % 100000}",
                'title': topic_title,
                'description': topic_description,
                'article_count': len(cluster_articles),
                'relevance': max(1, min(100, final_relevance)),  # Ensure 1-100 range with variation
                'articles': cluster_articles,  # Return ALL articles instead of just 3
                'semantic_cluster_id': cluster_id,
                'cohesion_score': float(cohesion)
            }
            
            topics.append(topic)
        
        return topics
    
    def _generate_topic_title(self, cluster_docs: List[Document]) -> str:
        """Generate a concise topic title from cluster documents"""
        # Extract common technical terms and concepts
        all_text = ' '.join([doc.page_content for doc in cluster_docs])
        
        # Technical term patterns optimized for semantic clustering
        tech_patterns = [
            r'\b(?:quantum|neural|deep|machine|artificial)\s+\w+\b',
            r'\b(?:transformer|bert|gpt|llm|generative)\s*(?:model|ai)?\b',
            r'\b(?:computer\s+vision|natural\s+language|reinforcement\s+learning)\b',
            r'\b(?:federated|meta|few-shot|zero-shot)\s+learning\b',
            r'\b(?:foundation|large\s+language)\s+models?\b'
        ]
        
        found_terms = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            found_terms.extend([match.strip() for match in matches])
        
        # Count term frequency and pick most common
        if found_terms:
            term_counts = Counter(found_terms)
            top_terms = [term for term, count in term_counts.most_common(3)]
            return ' & '.join(top_terms[:2]).title() if top_terms else "Emerging Tech Topic"
        
        # Fallback: extract from most representative title
        titles = [doc.metadata.get('title', '') for doc in cluster_docs if doc.metadata.get('title')]
        if titles:
            # Find common words in titles
            words = []
            for title in titles:
                words.extend(re.findall(r'\b[A-Za-z]{4,}\b', title))
            
            if words:
                word_counts = Counter(words)
                common_words = [word for word, count in word_counts.most_common(3) if count > 1]
                if common_words:
                    return ' '.join(common_words[:2]).title()
        
        return f"Topic {hash(' '.join([doc.page_content[:50] for doc in cluster_docs])) % 1000}"
    
    def _generate_topic_description(self, cluster_docs: List[Document], title: str) -> str:
        """Generate a descriptive summary of the topic cluster"""
        doc_count = len(cluster_docs)
        
        # Extract common themes
        abstracts = [doc.metadata.get('abstract', '') for doc in cluster_docs 
                    if doc.metadata.get('abstract')]
        
        if abstracts:
            # Simple theme extraction from abstracts
            common_words = []
            for abstract in abstracts:
                words = re.findall(r'\b[a-zA-Z]{5,}\b', abstract.lower())
                common_words.extend(words)
            
            if common_words:
                word_freq = Counter(common_words)
                themes = [word for word, count in word_freq.most_common(5) if count > 1]
                if themes:
                    return f"Emerging trend in {title.lower()} involving {', '.join(themes[:3])}"
        
        return f"Emerging research trend with {doc_count} related articles in {title.lower()}"
    
    def _rank_and_filter_topics(self, topics: List[Dict[str, Any]], 
                               min_frequency: int) -> List[Dict[str, Any]]:
        """Rank topics by relevance and filter by minimum frequency"""
        
        # Filter by minimum article count
        filtered_topics = [
            topic for topic in topics 
            if topic['article_count'] >= min_frequency
        ]
        
        # Sort by relevance score first, then by article count for tie-breaking
        filtered_topics.sort(
            key=lambda x: (x['relevance'], x['article_count']), 
            reverse=True
        )
        
        # Add rank information for frontend display
        for i, topic in enumerate(filtered_topics):
            topic['rank'] = i + 1
        
        return filtered_topics
    
    def _fetch_articles(self, feed_url: str, max_articles: int) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feed"""
        try:
            logger.info(f"Fetching articles from {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                return []
            
            articles = []
            for entry in feed.entries[:max_articles]:
                articles.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'description': entry.get('description', ''),
                    'published': entry.get('published', ''),
                    'author': entry.get('author', '')
                })
            
            logger.info(f"Successfully fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []

    def generate_topic_visualization(self, feed_url: str, max_articles: int = 50, 
                                   min_frequency: int = 2) -> Dict[str, Any]:
        """
        Generate PCA visualization data for topic relationships and overlap analysis.
        Returns 2D coordinates for topics and their relationships.
        """
        logger.info(f"Generating topic visualization with max_articles={max_articles}, min_frequency={min_frequency}")
        
        try:
            # First get the topics
            topics = self.extract_trending_topics(feed_url, max_articles, min_frequency)
            
            if len(topics) < 2:
                return {
                    "error": "Need at least 2 topics for visualization",
                    "topics_found": len(topics)
                }
            
            # Generate embeddings for each topic (title + description)
            topic_texts = []
            topic_info = []
            
            for topic in topics:
                # Combine title and description for richer representation
                topic_text = f"{topic['title']} {topic['description']}"
                topic_texts.append(topic_text)
                topic_info.append({
                    'id': topic['id'],
                    'title': topic['title'],
                    'article_count': topic['article_count'],
                    'relevance': topic['relevance']
                })
            
            # Generate embeddings
            if self.embeddings:
                embeddings_matrix = self._generate_embeddings(topic_texts)
                if embeddings_matrix is None:
                    return {"error": "Failed to generate embeddings for visualization"}
            else:
                return {"error": "Embeddings model not available"}
            
            # Apply PCA for 2D visualization
            if embeddings_matrix.shape[0] >= 2:
                # Use PCA to reduce to 2D
                pca = PCA(n_components=min(2, embeddings_matrix.shape[0], embeddings_matrix.shape[1]))
                pca_coords = pca.fit_transform(embeddings_matrix)
                
                # Calculate pairwise similarities for connection strength
                similarities = cosine_similarity(embeddings_matrix)
                
                # Prepare visualization data
                nodes = []
                edges = []
                
                for i, (coords, info) in enumerate(zip(pca_coords, topic_info)):
                    nodes.append({
                        'id': info['id'],
                        'title': info['title'],
                        'x': float(coords[0]),
                        'y': float(coords[1]),
                        'article_count': info['article_count'],
                        'relevance': info['relevance'],
                        'size': min(max(info['article_count'] * 2, 10), 50)  # Size based on article count
                    })
                
                # Create edges for similar topics (similarity > threshold)
                similarity_threshold = 0.3
                for i in range(len(topics)):
                    for j in range(i + 1, len(topics)):
                        similarity = similarities[i][j]
                        if similarity > similarity_threshold:
                            edges.append({
                                'source': topic_info[i]['id'],
                                'target': topic_info[j]['id'],
                                'strength': float(similarity),
                                'width': max(1, similarity * 5)  # Visual weight based on similarity
                            })
                
                return {
                    'nodes': nodes,
                    'edges': edges,
                    'pca_explained_variance': pca.explained_variance_ratio_.tolist(),
                    'total_topics': len(topics),
                    'total_connections': len(edges),
                    'visualization_type': 'pca_topic_network'
                }
            else:
                return {"error": "Insufficient data for PCA visualization"}
                
        except Exception as e:
            logger.error(f"Error generating topic visualization: {e}")
            return {"error": f"Visualization generation failed: {str(e)}"}

# Create service instance
langchain_trends_service = LangChainTrendsService(use_google_embeddings=False) 