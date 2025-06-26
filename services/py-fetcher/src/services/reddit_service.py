import feedparser
from typing import List
from datetime import datetime
from openapi_server.models.article import Article


class RedditFetcher:
    async def fetch(self, subreddit: str, max_results: int = 50) -> List[Article]:
        url = f"https://www.reddit.com/r/{subreddit}.rss"
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            # Parse published date if available
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except:
                    pass

            articles.append(Article(
                id=entry.id,
                title=entry.title,
                link=entry.link,
                summary=entry.summary,
                authors=[],  # Reddit posts don't have traditional authors
                published=published,
                source="reddit"
            ))
        return articles

reddit_fetcher = RedditFetcher()
