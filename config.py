"""
Configuration settings for AI Document Structurer
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Unified configuration class with dev-level settings for all environments"""
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Environment info (kept for logging purposes)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # Liberal timeouts and retries (formerly dev-level settings)
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

    # Generous token limits (formerly dev-level settings) - Increased for article processing
    MAX_TOKENS = {
        "Concise": int(os.getenv("MAX_TOKENS_CONCISE", "4000")),
        "Detailed": int(os.getenv("MAX_TOKENS_DETAILED", "8000")),
        "Comprehensive": int(os.getenv("MAX_TOKENS_COMPREHENSIVE", "12000"))
    }

def get_config():
    """Get the configuration instance"""
    return Config()

# Global configuration instance
app_config = get_config()