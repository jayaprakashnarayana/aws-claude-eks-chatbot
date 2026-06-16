import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API settings
    APP_NAME: str = "AWS Claude EKS Chatbot API"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # LLM Configuration Provider: "bedrock" or "anthropic"
    LLM_PROVIDER: str = "bedrock"

    # AWS Bedrock Config (used if LLM_PROVIDER is "bedrock")
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    # Anthropic API Config (used if LLM_PROVIDER is "anthropic")
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL_ID: str = "claude-3-5-sonnet-20240620"

    # CORS settings
    ALLOWED_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
