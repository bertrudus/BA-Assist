"""Pydantic data models for BA artifact analysis."""

from enum import Enum

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    REQUIREMENTS_DOCUMENT = "requirements_document"
    BUSINESS_PROCESS = "business_process"
    USER_STORY = "user_story"
    USE_CASE = "use_case"
    UNKNOWN = "unknown"


class DimensionScore(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    findings: list[str] = Field(default_factory=list)
    severity: str = Field(pattern=r"^(INFO|WARNING|CRITICAL)$")


class Issue(BaseModel):
    id: str
    dimension: str
    severity: str = Field(pattern=r"^(INFO|WARNING|CRITICAL)$")
    description: str
    location: str
    recommendation: str


class Suggestion(BaseModel):
    id: str
    original_text: str
    suggested_text: str
    rationale: str


class AnalysisResult(BaseModel):
    artifact_type: ArtifactType
    overall_score: float = Field(ge=0, le=100)
    dimensions: list[DimensionScore] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    suggestions: list[Suggestion] = Field(default_factory=list)
    iteration_number: int = 1


class UserStory(BaseModel):
    id: str
    epic: str
    title: str
    persona: str
    goal: str
    benefit: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: str = Field(pattern=r"^(Must|Should|Could|Won't)$")
    estimate_complexity: str = Field(pattern=r"^(S|M|L|XL)$")
    dependencies: list[str] = Field(default_factory=list)
    source_requirement_ids: list[str] = Field(default_factory=list)


class ComparisonReport(BaseModel):
    previous_iteration: int
    current_iteration: int
    previous_score: float
    current_score: float
    score_delta: float
    improved_dimensions: list[str] = Field(default_factory=list)
    regressed_dimensions: list[str] = Field(default_factory=list)
    resolved_issues: list[str] = Field(default_factory=list)
    new_issues: list[str] = Field(default_factory=list)


class CoverageReport(BaseModel):
    total_requirements: int
    covered_requirements: int
    uncovered_requirements: list[str] = Field(default_factory=list)
    coverage_percentage: float = Field(ge=0, le=100)
