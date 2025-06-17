from fastapi import FastAPI
from pydantic import BaseModel
import os, json, logging
from dotenv import load_dotenv
from google import genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY missing in .env")

# single client instance
google_client = genai.Client(api_key=GOOGLE_API_KEY)

logger = logging.getLogger(__name__)

app = FastAPI(title="NicheExplorer GenAI Service")

class ClassifyRequest(BaseModel):
    query: str

class ClassifyResponse(BaseModel):
    source: str  # "research" or "community"
    feed: str    # e.g. "cs.CV" or "computervision"

class DescribeRequest(BaseModel):
    keyword: str
    titles: list[str]

class DescribeResponse(BaseModel):
    description: str

RESEARCH_FEED = "https://rss.arxiv.org/rss/cs.CV"
COMMUNITY_FEED = "https://www.reddit.com/r/computervision/.rss"


def _classify_with_google(query: str):
    prompt = (
        "You are an assistant that decides which single RSS feed to query.\n"  # instruction
        "Return ONLY valid JSON with keys 'source' and 'feed'.\n"
        "- source: 'research' or 'community'.\n"
        "- feed: if research, give the arXiv subject ID only (e.g. cs.CV); if community, give the subreddit name only (e.g. computervision).\n"
        "User query: " + query
    )
    response = google_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    try:
        data = json.loads(response.text)
        return data.get("source", "research"), data.get("feed", "cs.CV")
    except Exception as e:
        logger.error("Failed to parse classify JSON: %s", e)
        # fallback
        return ("research", "cs.CV")


@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    try:
        source, feed = _classify_with_google(req.query)
    except Exception as e:
        logger.error("classify failed: %s", e)
        source, feed = "research", "cs.CV"

    return ClassifyResponse(source=source, feed=feed)


def _describe(keyword: str, titles: list[str]):
    joined = "\n".join(titles[:10])
    prompt = (
        f"The keyword '{keyword}' appears in the following article titles. "
        "Provide a concise (one sentence) explanation of why this keyword is an important trend in computer vision.\n"
        f"Titles:\n{joined}"
    )
    response = google_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text.strip()


@app.post("/describe", response_model=DescribeResponse)
def describe(req: DescribeRequest):
    desc = _describe(req.keyword, req.titles)
    return DescribeResponse(description=desc) 