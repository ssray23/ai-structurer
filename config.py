"""
Configuration settings for AI Document Structurer
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    # Environment detection - auto-detect production on Render
    ENVIRONMENT = os.getenv("ENVIRONMENT", 
                           "production" if os.getenv("RENDER") else "development").lower()
    IS_PRODUCTION = ENVIRONMENT == "production"
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Default timeouts and limits
    DEFAULT_API_TIMEOUT = 60
    DEFAULT_MAX_RETRIES = 3
    
    # Default token limits
    DEFAULT_TOKENS = {
        "Concise": 2000,
        "Detailed": 3500,
        "Comprehensive": 4500
    }

class DevelopmentConfig(Config):
    """Development/Local configuration"""
    DEBUG = True
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", Config.DEFAULT_API_TIMEOUT))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", Config.DEFAULT_MAX_RETRIES))
    
    # Generous limits for development
    MAX_TOKENS = {
        "Concise": int(os.getenv("MAX_TOKENS_CONCISE", Config.DEFAULT_TOKENS["Concise"])),
        "Detailed": int(os.getenv("MAX_TOKENS_DETAILED", Config.DEFAULT_TOKENS["Detailed"])),
        "Comprehensive": int(os.getenv("MAX_TOKENS_COMPREHENSIVE", Config.DEFAULT_TOKENS["Comprehensive"]))
    }

class ProductionConfig(Config):
    """Production configuration optimized for Render free tier"""
    DEBUG = False
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "20"))  # Very conservative for free tier
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "1"))  # Single retry to avoid cascading timeouts
    
    # Very reduced limits for production stability
    MAX_TOKENS = {
        "Concise": int(os.getenv("MAX_TOKENS_CONCISE", "1000")),
        "Detailed": int(os.getenv("MAX_TOKENS_DETAILED", "1500")),
        "Comprehensive": int(os.getenv("MAX_TOKENS_COMPREHENSIVE", "2000"))
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "1"))
    
    MAX_TOKENS = {
        "Concise": int(os.getenv("MAX_TOKENS_CONCISE", "500")),
        "Detailed": int(os.getenv("MAX_TOKENS_DETAILED", "1000")),
        "Comprehensive": int(os.getenv("MAX_TOKENS_COMPREHENSIVE", "1500"))
    }

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config():
    """Get the appropriate configuration based on environment"""
    # Use same logic as Config class for consistency
    environment = os.getenv("ENVIRONMENT", 
                           "production" if os.getenv("RENDER") else "development").lower()
    return config_map.get(environment, DevelopmentConfig)()

# Global configuration instance
app_config = get_config()