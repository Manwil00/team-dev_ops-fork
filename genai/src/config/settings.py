import os

class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    
    # API Configuration
    APP_TITLE: str = "NicheExplorer GenAI Service"
    
    # Model Configuration
    EMBEDDING_MODEL: str = "models/embedding-001"
    GENERATION_MODEL: str = "gemini-2.0-flash"
    
    # Feed URLs
    RESEARCH_FEED: str = "https://rss.arxiv.org/rss/cs.CV"
    COMMUNITY_FEED: str = "https://www.reddit.com/r/computervision/.rss"
    
    def __post_init__(self):
        if not self.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY missing in .env")

settings = Settings() 