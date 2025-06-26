import os

class GenAiSettings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    APP_TITLE: str = "NicheExplorer GenAI Service"

    EMBEDDING_MODEL: str = "models/embedding-001"
    GENERATION_MODEL: str = "gemini-2.0-flash"

    DEFAULT_RESEARCH_CATEGORY: str = "cs.CV"
    DEFAULT_COMMUNITY_FEED: str = "https://www.reddit.com/r/computervision/.rss"

settings = GenAiSettings()
