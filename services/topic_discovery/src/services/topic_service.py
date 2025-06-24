import httpx
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import hdbscan
import umap
import arxiv
import re
from collections import Counter
import re
from collections import Counter

class TopicDiscoveryService:
    def __init__(self, genai_base_url: str = "http://genai:8000"):
        self.genai_base_url = genai_base_url
        
    async def discover_topics(
        self, 
        query: str, 
        max_results: int = 50,
        min_cluster_size: int = 3,
        n_components: int = 15
    ) -> Dict[str, Any]:
        """
        Original method: Discover topics using external embeddings + HDBSCAN clustering
        """
        # Fetch articles from arXiv
        print(f"Searching arXiv for: {query}")
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        articles = []
        texts = []
        ids = []
        
        for result in search.results():
            article = {
                "id": result.get_short_id(),
                "title": result.title,
                "link": result.entry_id,
                "abstract": result.summary,
                "authors": [author.name for author in result.authors]
            }
            articles.append(article)
            texts.append(f"{result.title}. {result.summary}")
            ids.append(result.get_short_id())
        
        if len(articles) == 0:
            return {
                "topics": [],
                "total_articles": 0
            }
        
        print(f"Found {len(articles)} articles, getting embeddings...")
        
        # Get embeddings using batch endpoint with caching
        embeddings = await self._get_embeddings_batch(texts, ids)
        
        return self._cluster_and_label(articles, embeddings, min_cluster_size, n_components)

    async def discover_topics_with_keys(
        self,
        query: str,
        article_keys: List[str],
        articles: List[Dict[str, Any]],
        min_cluster_size: int = 3,
        n_components: int = 15
    ) -> Dict[str, Any]:
        """
        API-first method: Use batch endpoint with pre-fetched article keys
        """
        if len(articles) == 0:
            return {
                "topics": [],
                "total_articles": 0
            }
        
        print(f"Getting embeddings for {len(article_keys)} articles via batch API...")
        
        # Prepare texts and IDs for batch embedding
        texts = [f"{article['title']}. {article.get('abstract', '')}" for article in articles]
        
        # Use batch endpoint for efficient embedding with caching
        embeddings = await self._get_embeddings_batch(texts, article_keys)
        
        return self._cluster_and_label(articles, embeddings, min_cluster_size, n_components)

    def _cluster_and_label(
        self,
        articles: List[Dict[str, Any]],
        embeddings: np.ndarray,
        min_cluster_size: int,
        n_components: int
    ) -> Dict[str, Any]:
        """
        Common method for clustering and labeling topics
        """
        print(f"Clustering {len(embeddings)} embeddings...")
        
        # Use more dimensions for better separation of subtopics
        n_components = min(n_components, len(embeddings) - 1, 15)
        
        # Reduce dimensionality with UMAP - optimized for finding diverse subtopics
        reducer = umap.UMAP(
            n_components=n_components,
            random_state=42,
            metric='cosine',
            n_neighbors=min(15, len(embeddings) // 3),  # Adaptive neighbors
            min_dist=0.1,  # Allow tighter clusters for more specific subtopics
            spread=1.0
        )
        reduced_embeddings = reducer.fit_transform(embeddings)
        
        # Use smaller min_cluster_size to find more granular subtopics
        effective_min_size = max(2, min(min_cluster_size, len(embeddings) // 8))
        
        # Cluster with HDBSCAN - optimized for finding diverse subtopics within domain
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=effective_min_size,
            min_samples=max(1, effective_min_size - 1),
            metric='euclidean',
            cluster_selection_epsilon=0.05,  # Lower epsilon for more clusters
            alpha=1.0,
            cluster_selection_method='eom'  # Excess of Mass for better small cluster detection
        )
        
        cluster_labels = clusterer.fit_predict(reduced_embeddings)
        probabilities = clusterer.probabilities_
        
        # Group articles by cluster
        clusters = {}
        for i, (article, label, prob) in enumerate(zip(articles, cluster_labels, probabilities)):
            if label >= 0:  # Ignore noise points (-1)
                if label not in clusters:
                    clusters[label] = {
                        "articles": [],
                        "confidences": []
                    }
                clusters[label]["articles"].append(article)
                clusters[label]["confidences"].append(prob)
        
        print(f"Found {len(clusters)} clusters from {len(articles)} articles")
        
        # Generate meaningful topic labels 
        topics = []
        for cluster_id, cluster_data in clusters.items():
            cluster_articles = cluster_data["articles"]
            confidences = cluster_data["confidences"]
            
            # Generate meaningful topic title and description
            topic_info = self._generate_topic_info(cluster_articles)
            
            # Calculate confidence as average probability
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            topic = {
                "id": str(cluster_id),  # Convert to string for Java
                "title": topic_info["title"],
                "description": topic_info["description"],
                "article_count": len(cluster_articles),
                "relevance": round(avg_confidence * 100),  # Convert to int for Java (0-100 scale)
                "articles": cluster_articles
            }
            topics.append(topic)
        
        # Sort by relevance first, then by article count
        topics.sort(key=lambda t: (-t["relevance"], -t["article_count"]))
        
        return {
            "topics": topics,
            "total_articles": len(articles)
        }

    async def _get_embeddings_batch(self, texts: List[str], ids: List[str]) -> np.ndarray:
        """Get embeddings using batch endpoint with ChromaDB caching"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.genai_base_url}/embed-batch",
                json={"texts": texts, "ids": ids},
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"Batch embedding: {result['cached_count']}/{len(texts)} from cache")
            return np.array(result["vectors"])

    async def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings from genai service (fallback for single requests)"""
        embeddings = []
        
        async with httpx.AsyncClient() as client:
            for text in texts:
                response = await client.post(
                    f"{self.genai_base_url}/embed",
                    json={"text": text},
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                embeddings.append(result["vector"])
        
        return np.array(embeddings)

    def _generate_topic_info(self, articles: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate meaningful topic title and description using multiple strategies"""
        if not articles:
            return {"title": "Unknown Topic", "description": "No articles available"}
        
        try:
            # Combine all titles and abstracts
            all_titles = [article['title'] for article in articles]
            all_texts = [f"{article['title']} {article.get('abstract', '')}" for article in articles]
            
            print(f"Generating topic for {len(articles)} articles")
            print(f"Sample titles: {all_titles[:2]}")
            
            # Strategy 1: Extract key phrases from titles (most informative)
            title_keyphrases = self._extract_keyphrases_from_titles(all_titles)
            print(f"Title keyphrases: {title_keyphrases[:5]}")
            
            # Strategy 2: Find technical terms and methods from abstracts
            technical_terms = self._extract_technical_terms(all_texts)
            print(f"Technical terms: {technical_terms[:5]}")
            
            # Strategy 3: Use TF-IDF on meaningful n-grams
            tfidf_phrases = self._extract_tfidf_phrases(all_texts)
            print(f"TF-IDF phrases: {tfidf_phrases[:5]}")
            
            # Combine and rank all candidates
            all_candidates = title_keyphrases + technical_terms + tfidf_phrases
            print(f"All candidates: {all_candidates[:10]}")
            
            # Select best title and generate description
            if all_candidates:
                # Pick most frequent or highest scoring phrase
                candidate_scores = Counter(all_candidates)
                best_candidates = candidate_scores.most_common(5)
                print(f"Best candidates: {best_candidates}")
                
                best_title = best_candidates[0][0]
                
                # Clean up the title
                title = self._clean_topic_title(best_title)
                print(f"Final title: {title}")
                
                # Generate description
                description = self._generate_description(articles, technical_terms[:3])
                
                return {"title": title, "description": description}
            else:
                print("No candidates found, using fallback")
                # Fallback to simple approach
                return self._fallback_topic_generation(articles)
                
        except Exception as e:
            print(f"Error generating topic info: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_topic_generation(articles)

    def _extract_keyphrases_from_titles(self, titles: List[str]) -> List[str]:
        """Extract meaningful phrases from paper titles"""
        keyphrases = []
        
        for title in titles:
            # Clean title
            title = re.sub(r'[^\w\s-]', ' ', title.lower())
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Extract meaningful phrases (2-4 words)
            words = title.split()
            
            # Extract bigrams and trigrams that look like technical terms
            for i in range(len(words) - 1):
                bigram = ' '.join(words[i:i+2])
                if self._is_meaningful_phrase(bigram):
                    keyphrases.append(bigram)
                    
                if i < len(words) - 2:
                    trigram = ' '.join(words[i:i+3])
                    if self._is_meaningful_phrase(trigram):
                        keyphrases.append(trigram)
        
        return keyphrases

    def _extract_technical_terms(self, texts: List[str]) -> List[str]:
        """Extract technical terms and methods from abstracts"""
        technical_terms = []
        
        # Common patterns for technical terms in CS/AI papers
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized terms
            r'\b\w+(?:\s+\w+)*\s+(?:network|model|algorithm|method|approach|framework|system)\b',
            r'\b(?:deep|machine|reinforcement|supervised|unsupervised)\s+learning\b',
            r'\b(?:neural|convolutional|recurrent|transformer)\s+\w+\b',
            r'\b\w+(?:\s+\w+)*\s+(?:detection|recognition|segmentation|classification|prediction)\b'
        ]
        
        all_text = ' '.join(texts).lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                if self._is_meaningful_phrase(match):
                    technical_terms.append(match.lower().strip())
        
        return list(set(technical_terms))

    def _extract_tfidf_phrases(self, texts: List[str]) -> List[str]:
        """Extract meaningful phrases using TF-IDF on n-grams"""
        try:
            # Use TF-IDF on bigrams and trigrams
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=50,
                ngram_range=(2, 3),  # Bigrams and trigrams
                min_df=1,
                max_df=0.8,
                lowercase=True
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores
            avg_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Get top phrases
            top_indices = avg_scores.argsort()[-10:][::-1]
            top_phrases = [feature_names[i] for i in top_indices if avg_scores[i] > 0]
            
            return [phrase for phrase in top_phrases if self._is_meaningful_phrase(phrase)]
            
        except Exception as e:
            print(f"TF-IDF extraction error: {e}")
            return []

    def _is_meaningful_phrase(self, phrase: str) -> bool:
        """Check if a phrase is meaningful for topic labeling"""
        phrase = phrase.strip().lower()
        
        # Filter out common stop words and generic terms
        stop_terms = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'paper', 'study', 'work', 'research', 'approach', 'method', 'result', 'results',
            'analysis', 'evaluation', 'experiment', 'experiments', 'performance', 'based',
            'using', 'used', 'propose', 'proposed', 'present', 'presented', 'show', 'shows'
        }
        
        # Must be at least 2 characters and not all numbers
        if len(phrase) < 2 or phrase.isdigit():
            return False
            
        # Must not be just stop words
        words = phrase.split()
        if all(word in stop_terms for word in words):
            return False
            
        # Must contain at least one meaningful word
        return any(len(word) > 2 and word not in stop_terms for word in words)

    def _clean_topic_title(self, title: str) -> str:
        """Clean and format topic title"""
        # Clean up and capitalize properly
        title = re.sub(r'[^\w\s-]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Capitalize first letter of each word for technical terms
        words = title.split()
        cleaned_words = []
        
        for word in words:
            if len(word) > 1:
                cleaned_words.append(word.capitalize())
            else:
                cleaned_words.append(word.lower())
                
        result = ' '.join(cleaned_words)
        
        # Limit length
        if len(result) > 50:
            result = result[:47] + "..."
            
        return result if result else "Research Topic"

    def _generate_description(self, articles: List[Dict[str, Any]], key_terms: List[str]) -> str:
        """Generate a meaningful description for the topic"""
        count = len(articles)
        
        if key_terms:
            main_focus = ', '.join(key_terms[:2])
            return f"Research cluster focusing on {main_focus} ({count} papers)"
        else:
            return f"Research cluster with {count} related papers"

    def _fallback_topic_generation(self, articles: List[Dict[str, Any]]) -> Dict[str, str]:
        """Fallback method when advanced extraction fails"""
        count = len(articles)
        return {
            "title": f"Research Cluster {count}",
            "description": f"Collection of {count} related research papers"
        }

    async def discover_topics_from_cached_embeddings(
        self,
        query: str,
        article_keys: List[str],
        articles: List[Dict[str, Any]],
        min_cluster_size: int = 3,
        n_components: int = 15
    ) -> Dict[str, Any]:
        """
        Proper REST architecture: Use cached embeddings from GenAI service
        This method assumes embeddings are already cached in ChromaDB by the GenAI service
        """
        if len(articles) == 0:
            return {
                "topics": [],
                "total_articles": 0
            }
        
        print(f"Retrieving {len(article_keys)} cached embeddings from GenAI service...")
        
        # Get cached embeddings from GenAI service
        embeddings = await self._get_cached_embeddings_from_genai(article_keys)
        
        if len(embeddings) == 0 or all(len(emb) == 0 for emb in embeddings):
            print("No cached embeddings found, cannot proceed with topic discovery")
            return {
                "topics": [],
                "total_articles": 0
            }
        
        # Filter out articles with empty embeddings
        valid_articles = []
        valid_embeddings = []
        for article, embedding in zip(articles, embeddings):
            if len(embedding) > 0:
                valid_articles.append(article)
                valid_embeddings.append(embedding)
        
        if len(valid_articles) == 0:
            return {
                "topics": [],
                "total_articles": 0
            }
        
        print(f"Using {len(valid_embeddings)} cached embeddings for clustering")
        embeddings_array = np.array(valid_embeddings)
        
        return self._cluster_and_label(valid_articles, embeddings_array, min_cluster_size, n_components)

    async def _get_cached_embeddings_from_genai(self, article_keys: List[str]) -> List[List[float]]:
        """Get cached embeddings from GenAI service by article IDs"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.genai_base_url}/embeddings-by-ids",
                json={"ids": article_keys},
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"Retrieved {result['found_count']}/{len(article_keys)} embeddings from cache")
            return result["embeddings"]

# Global instance
topic_service = TopicDiscoveryService()