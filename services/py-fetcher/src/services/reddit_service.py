import feedparser
from typing import List
from datetime import datetime
from niche_explorer_models.models.article import Article


class RedditFetcher:
    async def fetch(self, subreddit: str, max_results: int = 50) -> List[Article]:
        url = f"https://www.reddit.com/r/{subreddit}.rss"
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            # Parse published date if available
            published = None
            if entry.get("published_parsed"):
                try:
                    published = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass
            # Fallback to updated if published is not available
            elif entry.get("updated_parsed"):
                try:
                    published = datetime(*entry.updated_parsed[:6])
                except Exception:
                    pass

            articles.append(
                Article(
                    id=entry.id,
                    title=entry.title,
                    link=entry.link,
                    summary=entry.summary,
                    authors=[],  # Reddit posts don't have traditional authors
                    published=published,
                    source="reddit",
                )
            )
        return articles


reddit_fetcher = RedditFetcher()
