from fastapi import FastAPI, HTTPException
from niche_explorer_models.models.article_fetch_request import ArticleFetchRequest
from niche_explorer_models.models.article_fetch_response import ArticleFetchResponse

import logging
from .services.arxiv_service import arxiv_fetcher
from .services.reddit_service import reddit_fetcher

logger = logging.getLogger("article_fetcher")
# Enable debug logging by default (can be overridden by container env)
logging.basicConfig(level=logging.DEBUG)

# Initialize FastAPI app with metadata matching OpenAPI spec
app = FastAPI(
    title="NicheExplorer Article Fetcher Service",
    version="1.0.0",
    description="Fetches articles from arXiv and Reddit based on queries"
)

@app.post("/api/v1/articles", response_model=ArticleFetchResponse)
async def fetch_articles(request: ArticleFetchRequest):
    """Fetch articles from the specified source"""
    try:
        logger.info(
            f"Received fetch request: source={request.source}, query={request.query}, category={request.category}, limit={request.limit}"
        )

        # Determine how many articles to fetch (default to 50 if not provided)
        max_results = request.limit or 50

        # ------------------------------------------------------------------
        # Source-specific routing
        # ------------------------------------------------------------------
        if request.source == "arxiv":
            # If category already looks like an advanced arXiv query (contains cat: or all:), use as-is
            if request.category and ("cat:" in request.category or "all:" in request.category):
                search_query = request.category
            else:
                # Plain category name provided → build simple category query; otherwise fall back to free-text
                search_query = f"cat:{request.category}" if request.category else request.query
            articles = await arxiv_fetcher.fetch(search_query, max_results)

            # ------------------------------------------------------------------
            # Multi-step fallback to avoid empty result sets
            # 1) advanced query (already executed)
            # 2) category-only (cat:xyz)
            # 3) free-text query
            # ------------------------------------------------------------------

            if len(articles) == 0 and request.category:
                # Detect advanced form containing both phrase/all: and cat:
                if "cat:" in request.category and ("all:" in request.category or "AND" in request.category):
                    # Extract the last category token after 'cat:' (handles URL-encoded '+' already replaced by Space)
                    cat_part = request.category.split("cat:")[-1]
                    fallback_query = f"cat:{cat_part}"
                    logger.info("Advanced query empty – retrying category-only '%s'", fallback_query)
                    articles = await arxiv_fetcher.fetch(fallback_query, max_results)

            if len(articles) == 0:
                free_text_query = request.query
                if free_text_query:
                    logger.info("Category query empty – retrying free-text '%s'", free_text_query)
                    articles = await arxiv_fetcher.fetch(free_text_query, max_results)

            if len(articles) == 0:
                logger.warning("ArXiv query ultimately returned 0 results for original query '%s'", search_query)
        elif request.source == "reddit":
            # Treat `category` as subreddit (fallback to free-text query if absent)
            subreddit = request.category or request.query
            articles = await reddit_fetcher.fetch(subreddit, max_results)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {request.source}")
        
        logger.info(f"Fetched {len(articles)} articles from {request.source}")
        
        return ArticleFetchResponse(
            articles=articles,
            total_found=len(articles),
            source=request.source
        )
    except Exception as e:
        logger.error(f"Failed to fetch articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}")

@app.get("/api/v1/sources/{source}/categories")
async def get_source_categories(source: str):
    """Get available categories for a specific data source"""
    if source == "arxiv":
        return {
            "Computer Science": [
                "cs.AI", "cs.AR", "cs.CC", "cs.CE", "cs.CG", "cs.CL", "cs.CR", "cs.CV", "cs.CY", "cs.DB", 
                "cs.DC", "cs.DL", "cs.DM", "cs.DS", "cs.ET", "cs.FL", "cs.GL", "cs.GR", "cs.GT", "cs.HC",
                "cs.IR", "cs.IT", "cs.LG", "cs.LO", "cs.MA", "cs.MM", "cs.MS", "cs.NA", "cs.NE", "cs.NI",
                "cs.OH", "cs.OS", "cs.PF", "cs.PL", "cs.RO", "cs.SC", "cs.SD", "cs.SE", "cs.SI", "cs.SY"
            ],
            "Economics": ["econ.EM", "econ.GN", "econ.TH"],
            "Electrical Engineering and Systems Science": ["eess.AS", "eess.IV", "eess.SP", "eess.SY"],
            "Mathematics": [
                "math.AC", "math.AG", "math.AP", "math.AT", "math.CA", "math.CO", "math.CT", "math.CV",
                "math.DG", "math.DS", "math.FA", "math.GM", "math.GN", "math.GR", "math.GT", "math.HO",
                "math.IT", "math.KT", "math.LO", "math.MG", "math.MP", "math.NA", "math.NT", "math.OA",
                "math.OC", "math.PR", "math.QA", "math.RA", "math.RT", "math.SG", "math.SP", "math.ST"
            ],
            "Physics": ["astro-ph.CO", "astro-ph.EP", "astro-ph.GA", "astro-ph.HE", "astro-ph.IM", "astro-ph.SR",
                       "cond-mat.dis-nn", "cond-mat.mes-hall", "cond-mat.mtrl-sci", "cond-mat.other",
                       "cond-mat.quant-gas", "cond-mat.soft", "cond-mat.stat-mech", "cond-mat.str-el", "cond-mat.supr-con",
                       "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph",
                       "nlin.AO", "nlin.CD", "nlin.CG", "nlin.PS", "nlin.SI",
                       "nucl-ex", "nucl-th",
                       "physics.acc-ph", "physics.ao-ph", "physics.app-ph", "physics.atm-clus", "physics.atom-ph",
                       "physics.bio-ph", "physics.chem-ph", "physics.class-ph", "physics.comp-ph", "physics.data-an",
                       "physics.ed-ph", "physics.flu-dyn", "physics.gen-ph", "physics.geo-ph", "physics.hist-ph",
                       "physics.ins-det", "physics.med-ph", "physics.optics", "physics.plasm-ph", "physics.pop-ph",
                       "physics.soc-ph", "physics.space-ph",
                       "quant-ph"],
            "Quantitative Biology": ["q-bio.BM", "q-bio.CB", "q-bio.GN", "q-bio.MN", "q-bio.NC", "q-bio.OT",
                                   "q-bio.PE", "q-bio.QM", "q-bio.SC", "q-bio.TO"],
            "Quantitative Finance": ["q-fin.CP", "q-fin.EC", "q-fin.GN", "q-fin.MF", "q-fin.PM", "q-fin.PR",
                                   "q-fin.RM", "q-fin.ST", "q-fin.TR"],
            "Statistics": ["stat.AP", "stat.CO", "stat.ME", "stat.ML", "stat.OT", "stat.TH"]
        }
    else:
        # Return empty list for other sources for now
        return {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
