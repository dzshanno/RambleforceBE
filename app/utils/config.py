from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str
    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str
    POSTGRES_DB: str = "mydb"
    POSTGRES_USER: str = "dbuser"
    POSTGRES_PASSWORD: str = "dummy-password"

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
    ANTHROPIC_MODEL: str = "gpt-3.5-turbo"

    # WhatsApp settings
    WHATSAPP_API_KEY: Optional[str] = None
    WHATSAPP_PHONE_NUMBER: Optional[str] = None

    # STRIPE settings
    STRIPE_SECRET_KEY: str = "your_stripe_secret_key"
    STRIPE_WEBHOOK_SECRET: str = "your_stripe_webhook_secret"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
