from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AWS settings
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "eu-west-2"
    S3_BUCKET: str = "rambleforce25-assets"

    # Anthropic settings
    ANTHROPIC_API_KEY: str

    # WhatsApp settings
    WHATSAPP_API_KEY: Optional[str] = None
    WHATSAPP_PHONE_NUMBER: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
