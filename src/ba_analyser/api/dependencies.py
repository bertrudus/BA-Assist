"""Shared FastAPI dependencies: client factory, settings, analyser factory."""

from functools import lru_cache

from ba_analyser.analysers.process_analyser import ProcessAnalyser
from ba_analyser.analysers.requirements_analyser import RequirementsAnalyser
from ba_analyser.analysers.story_analyser import StoryAnalyser
from ba_analyser.config import Settings
from ba_analyser.models import ArtifactType


@lru_cache
def get_settings() -> Settings:
    return Settings()


def create_client(settings: Settings | None = None):
    """Create the appropriate LLM client based on configuration."""
    settings = settings or get_settings()
    if settings.llm_provider == "anthropic":
        from ba_analyser.anthropic_client import AnthropicClient
        return AnthropicClient(config=settings)
    else:
        from ba_analyser.bedrock_client import BedrockClient
        return BedrockClient(config=settings)


def get_analyser(artifact_type: ArtifactType, client=None):
    """Return the appropriate analyser for the artifact type."""
    client = client or create_client()
    analysers = {
        ArtifactType.REQUIREMENTS_DOCUMENT: RequirementsAnalyser,
        ArtifactType.BUSINESS_PROCESS: ProcessAnalyser,
        ArtifactType.USER_STORY: StoryAnalyser,
    }
    analyser_cls = analysers.get(artifact_type, RequirementsAnalyser)
    return analyser_cls(client)
