"""Request / response Pydantic models for the API layer."""

from pydantic import BaseModel, Field

from ba_analyser.models import ArtifactType


class AnalyseRequest(BaseModel):
    artifact_text: str
    artifact_type: ArtifactType | None = None
    threshold: float = 80.0


class DetectTypeRequest(BaseModel):
    artifact_text: str


class DetectTypeResponse(BaseModel):
    artifact_type: ArtifactType
    confidence: float = 0.0


class GenerateStoriesRequest(BaseModel):
    artifact_text: str


class RefineStoryRequest(BaseModel):
    story_id: str
    feedback: str


class ExportRequest(BaseModel):
    format: str = "markdown"


class CompareRequest(BaseModel):
    artifact_text_1: str
    artifact_text_2: str


class SessionCreateRequest(BaseModel):
    artifact_text: str
    threshold: float = 80.0


class ApplySuggestionsRequest(BaseModel):
    accepted_suggestion_ids: list[str]


class ConfigUpdateRequest(BaseModel):
    llm_provider: str | None = None
    anthropic_model_id: str | None = None
    bedrock_model_id: str | None = None
    bedrock_temperature_analysis: float | None = None
    bedrock_temperature_generation: float | None = None
    analysis_quality_threshold: float | None = None
