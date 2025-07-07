# ---------------------------------------------------------------------------
# ArXiv fetching utility
# ---------------------------------------------------------------------------

import arxiv
import requests
import feedparser
from datetime import datetime, timezone
from typing import List
from niche_explorer_models.models.article import Article
from urllib.parse import quote


class ArxivFetcher:
    """Fetch papers from arXiv."""

    def __init__(self, page_size: int = 100):
        """Create a client with sensible retry & throttling defaults.

        The upstream arXiv API imposes rate-limits (1 request/sec). The official
        `arxiv` Python package provides built-in back-off via the `delay_seconds`
        parameter. We also enable a small number of automatic retries to handle
        transient network errors while still failing fast when the query itself
        is invalid.
        """
        self.client = arxiv.Client(
            page_size=page_size, num_retries=3, delay_seconds=1.0
        )

    async def fetch(self, query: str, max_results: int = 50) -> List[Article]:
        import logging

        logger = logging.getLogger(__name__)

        try:
            search = arxiv.Search(query=query, max_results=max_results)
            results = list(self.client.results(search))
        except arxiv.ArxivError as err:
            logger.warning(
                "arxiv library error for '%s' – %s. Falling back to HTTP API.",
                query,
                err,
            )
            results = []

        # If the primary attempt yielded no results, fall back to direct HTTP API call.
        if len(results) == 0:
            logger.info(
                "No arxiv-library results for '%s'. Falling back to export.arxiv.org API",
                query,
            )
            return await self._fetch_via_http_api(query, max_results)

        return [self._map_result(r) for r in results]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_result(self, res: arxiv.Result) -> Article:
        # Ensure timezone-aware datetime (UTC) for JSON serialisation
        published = res.published
        if published and published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)

        return Article(
            id=res.get_short_id(),
            title=res.title,
            link=res.entry_id,
            summary=res.summary,
            authors=[a.name for a in res.authors],
            published=published,
            source="arxiv",
        )

    # ------------------------------------------------------------------
    # Fallback via raw HTTP request (XML feed) – synchronous call inside async
    # context is acceptable for this lightweight service.
    # ------------------------------------------------------------------

    async def _fetch_via_http_api(self, query: str, max_results: int) -> List[Article]:
        """Call the export.arxiv.org REST API directly and parse the Atom feed."""
        base = "https://export.arxiv.org/api/query"

        # Manual encoding: spaces → %20, leave '+' intact so Boolean operators
        # such as '+AND+' survive. Also keep colon ':' and quotes '"'.
        encoded_query = quote(query, safe=':+"')
        url = (
            f"{base}?search_query={encoded_query}"
            f"&id_list="
            f"&sortBy=relevance&sortOrder=descending&start=0&max_results={max_results}"
        )

        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        articles: List[Article] = []
        for entry in feed.entries:
            published = None
            if hasattr(entry, "published"):
                try:
                    published = datetime.strptime(
                        entry.published, "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=timezone.utc)
                except Exception:
                    published = None

            articles.append(
                Article(
                    id=entry.id.split("/")[-1],
                    title=entry.title,
                    link=entry.id,
                    summary=entry.summary,
                    authors=[a.name for a in entry.authors]
                    if hasattr(entry, "authors")
                    else [],
                    published=published,
                    source="arxiv",
                )
            )
        return articles


arxiv_fetcher = ArxivFetcher()
