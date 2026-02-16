"""Config router — GET/PUT application settings."""

from fastapi import APIRouter

from ba_analyser.api.dependencies import get_settings

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
def get_config():
    settings = get_settings()
    return {
        "llm_provider": settings.llm_provider,
        "anthropic_model_id": settings.anthropic_model_id,
        "anthropic_api_key_set": bool(settings.anthropic_api_key),
        "bedrock_model_id": settings.bedrock_model_id,
        "aws_region": settings.aws_region,
        "bedrock_max_tokens": settings.bedrock_max_tokens,
        "bedrock_temperature_analysis": settings.bedrock_temperature_analysis,
        "bedrock_temperature_generation": settings.bedrock_temperature_generation,
        "analysis_quality_threshold": settings.analysis_quality_threshold,
    }
