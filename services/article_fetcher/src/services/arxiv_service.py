# ---------------------------------------------------------------------------
# ArXiv fetching utility
# ---------------------------------------------------------------------------

import arxiv
import feedparser
import requests
from typing import List, Dict, Any


class ArxivFetcher:
    """Fetch papers from arXiv.

    The official `arxiv` Python package sometimes raises `HTTPError` for the
    recent *HTTP ➜ HTTPS* redirect at export.arxiv.org.  We transparently retry
    using an HTTPS request and parse the resulting Atom feed with `feedparser`
    to keep the service resilient.
    """

    def __init__(self):
        # default client from the library
        self.client = arxiv.Client()

    async def fetch(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            results = self.client.results(search)
            return [self._map_result(r) for r in results]

        except arxiv.HTTPError as err:
            # Handle 301 redirect edge-case gracefully
            if "HTTP 301" in str(err):
                return await self._fetch_via_https_fallback(query, max_results)
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_via_https_fallback(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        base = "https://export.arxiv.org/api/query"
        params = {
            "search_query": query,
            "id_list": "",
            "sortBy": "relevance",
            "sortOrder": "descending",
            "start": 0,
            "max_results": max_results,
        }
        resp = requests.get(base, params=params, timeout=30)
        resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        articles = []
        for entry in feed.entries:
            articles.append({
                "id": entry.id.split('/')[-1],
                "title": entry.title,
                "link": entry.id,
                "abstract": entry.summary,
                "authors": [a.name for a in entry.authors] if hasattr(entry, "authors") else [],
            })
        return articles

    def _map_result(self, res: arxiv.Result) -> Dict[str, Any]:
        return {
            "id": res.get_short_id(),
            "title": res.title,
            "link": res.entry_id,
            "abstract": res.summary,
            "authors": [a.name for a in res.authors],
        }

arxiv_fetcher = ArxivFetcher() 