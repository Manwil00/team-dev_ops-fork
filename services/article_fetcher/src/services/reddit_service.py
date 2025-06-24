import feedparser
from typing import List, Dict

class RedditFetcher:
    async def fetch(self, subreddit: str, max_results: int = 50) -> List[Dict]:
        url = f"https://www.reddit.com/r/{subreddit}.rss"
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            articles.append({
                "id": entry.id,
                "title": entry.title,
                "link": entry.link,
                "abstract": entry.summary,
                "authors": []
            })
        return articles

reddit_fetcher = RedditFetcher() 