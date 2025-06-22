import os
from dotenv import load_dotenv

# Load .env file from the root directory (go up 3 levels from this file)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    
    # API Configuration
    APP_TITLE: str = "NicheExplorer GenAI Service"
    
    # Model Configuration
    EMBEDDING_MODEL: str = "models/embedding-001"
    GENERATION_MODEL: str = "gemini-2.0-flash"
    
    # Default ArXiv categories and Reddit feeds
    DEFAULT_RESEARCH_CATEGORY: str = "cs.CV"
    DEFAULT_COMMUNITY_FEED: str = "https://www.reddit.com/r/computervision/.rss"
    
    def __post_init__(self):
        if not self.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY missing in .env")

settings = Settings() 