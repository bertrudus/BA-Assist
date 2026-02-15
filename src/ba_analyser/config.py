"""Application settings loaded from environment variables and .env files."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # AWS
    aws_region: str = "eu-west-2"
    aws_profile: str | None = None

    # Bedrock
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_max_tokens: int = 4096
    bedrock_temperature_analysis: float = 0.1
    bedrock_temperature_generation: float = 0.4

    # Analysis
    analysis_quality_threshold: float = 80.0
