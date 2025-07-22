from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

API_BASE = os.getenv("API_BASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
r2_token = os.getenv("R2_TOKEN")
r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")
r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
r2_bucket_name = os.getenv("R2_BUCKET_NAME")
r2_endpoint_url = os.getenv("R2_ENDPOINT_URL")
r2_region = os.getenv("R2_REGION")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRE_MINUTES = os.getenv("JWT_EXPIRE_MINUTES")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_PORT = os.getenv("MAIL_PORT")
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME") or "NEU Course Scheduler"

print(f"Using API base URL: {API_BASE}")
print(f"Using Redis URL: {'***' if REDIS_URL else 'Not set'}")
print(f"Using OpenAI API key: {'***' if OPENAI_API_KEY else 'Not set'}")
print(f"Using R2 bucket name: {'***' if r2_bucket_name else 'Not set'}")
print(f"Using R2 endpoint URL: {'***' if r2_endpoint_url else 'Not set'}")
print(f"Using R2 region: {'***' if r2_region else 'Not set'}")
print(f"Using R2 access key ID: {'***' if r2_access_key_id else 'Not set'}")
print(f"Using R2 secret access key: {'***' if r2_secret_access_key else 'Not set'}")
print(f"Using R2 token: {'***' if r2_token else 'Not set'}")
print(f"Using Mailtrap username: {'***' if MAIL_USERNAME else 'Not set'}")
print(f"Using Mailtrap password: {'***' if MAIL_PASSWORD else 'Not set'}")
print(f"Using Mailtrap from address: {'***' if MAIL_FROM else 'Not set'}")
print(f"Using Mailtrap port: {'***' if MAIL_PORT else 'Not set'}")
print(f"Using Mailtrap server: {'***' if MAIL_SERVER else 'Not set'}")
print(f"Using Mailtrap from name: {'***' if MAIL_FROM_NAME else 'Not set'}")


class Settings(BaseSettings):
    # redis configuration
    redis_url: str = REDIS_URL
    celery_broker_url: str = REDIS_URL
    # OpenAI configuration
    openai_api_key: Optional[str] = OPENAI_API_KEY
    # R2 configuration
    r2_token: str = r2_token
    r2_access_key_id: str = r2_access_key_id
    r2_secret_access_key: str = r2_secret_access_key
    r2_bucket_name: str = r2_bucket_name
    r2_endpoint_url: str = r2_endpoint_url
    r2_region: str = r2_region
    # NU Banner configuration
    nu_banner_base_url: str = API_BASE
    # JWT configuration
    jwt_secret_key: str = JWT_SECRET_KEY
    jwt_algorithm: str = JWT_ALGORITHM
    jwt_expire_minutes: int = JWT_EXPIRE_MINUTES
    # Mailtrap configuration
    mail_username: str = MAIL_USERNAME
    mail_password: str = MAIL_PASSWORD
    mail_port: int = MAIL_PORT
    mail_server: str = MAIL_SERVER
    mail_from: str = MAIL_FROM
    mail_from_name: str = MAIL_FROM_NAME
    # OTP settings
    otp_length: int = 6
    otp_expire_minutes: int = 15
    # App settings
    debug: bool = False
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()
