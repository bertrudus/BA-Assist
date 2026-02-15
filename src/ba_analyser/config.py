"""Application settings loaded from environment variables and .env files."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Provider selection: "bedrock" or "anthropic"
    llm_provider: str = "bedrock"

    # AWS / Bedrock
    aws_region: str = "eu-west-2"
    aws_profile: str | None = None
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # Anthropic API
    anthropic_api_key: str | None = None
    anthropic_model_id: str = "claude-sonnet-4-5-20250929"

    # Shared model settings
    bedrock_max_tokens: int = 4096
    bedrock_temperature_analysis: float = 0.1
    bedrock_temperature_generation: float = 0.4

    # Analysis
    analysis_quality_threshold: float = 80.0
