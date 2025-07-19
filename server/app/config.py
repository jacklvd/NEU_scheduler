from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

API_BASE = os.getenv("API_BASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"Using API base URL: {API_BASE}")
print(f"Using Redis URL: {'***' if REDIS_URL else 'Not set'}")
print(f"Using OpenAI API key: {'***' if OPENAI_API_KEY else 'Not set'}")


class Settings(BaseSettings):
    # database_url: str
    redis_url: str = REDIS_URL
    celery_broker_url: str = REDIS_URL
    openai_api_key: Optional[str] = OPENAI_API_KEY
    nu_banner_base_url: str = API_BASE
    jwt_secret_key: str = "development-secret-key-change-in-production"
    jwt_algorithm: str = ""
    jwt_expire_minutes: int = 30
    # App settings
    debug: bool = False
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()
