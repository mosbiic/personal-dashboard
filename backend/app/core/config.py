from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Personal Dashboard"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/dashboard"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys
    TRELLO_API_KEY: str = ""
    TRELLO_TOKEN: str = ""
    GITHUB_TOKEN: str = ""
    OPENWEATHER_API_KEY: str = ""
    
    # Trello
    TRELLO_BOARD_ID: str = ""
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
