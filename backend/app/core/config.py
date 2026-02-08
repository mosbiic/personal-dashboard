from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Personal Dashboard"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/dashboard"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # 5 minutes default cache
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:5173/auth/github/callback"
    GITHUB_TOKEN: str = ""  # Personal access token (fallback)
    GITHUB_USERNAME: str = "mosbiic"
    
    # Trello
    TRELLO_API_KEY: str = ""
    TRELLO_TOKEN: str = ""
    TRELLO_BOARD_ID: str = ""
    
    # Weather
    OPENWEATHER_API_KEY: str = ""
    
    # Encryption (for sensitive tokens)
    ENCRYPTION_KEY: str = ""  # 32-byte base64 encoded key
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
