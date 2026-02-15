"""Base analyser with shared logic for all artifact types."""

import json
import logging
from abc import ABC, abstractmethod

from ba_analyser.models import (
    AnalysisResult,
    ArtifactType,
    DimensionScore,
    Issue,
    Suggestion,
)

logger = logging.getLogger(__name__)


class BaseAnalyser(ABC):
    """Base class for artifact analysers.

    Subclasses provide artifact_type, prompts, and dimension config.
    The analysis pipeline (evaluate per dimension → synthesise) is shared.
    """

    def __init__(self, client) -> None:
        self.client = client

    @property
    @abstractmethod
    def artifact_type(self) -> ArtifactType: ...

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @property
    @abstractmethod
    def dimension_prompts(self) -> dict[str, str]: ...

    @property
    @abstractmethod
    def synthesis_prompt(self) -> str: ...

    @property
    @abstractmethod
    def dimension_display_names(self) -> dict[str, str]: ...

    def analyse(
        self,
        artifact_text: str,
        iteration_number: int = 1,
    ) -> AnalysisResult:
        """Run full analysis across all dimensions and synthesise results."""
        dimension_results: dict[str, dict] = {}
        for dimension_name in self.dimension_prompts:
            logger.info("Evaluating dimension: %s", dimension_name)
            result = self._evaluate_dimension(artifact_text, dimension_name)
            dimension_results[dimension_name] = result

        logger.info("Synthesising dimension results")
        synthesis = self._synthesise(artifact_text, dimension_results)

        return self._build_result(synthesis, dimension_results, iteration_number)

    def _evaluate_dimension(
        self, artifact_text: str, dimension_name: str
    ) -> dict:
        prompt_template = self.dimension_prompts[dimension_name]
        user_prompt = prompt_template.format(artifact_text=artifact_text)

        messages = [
            {"role": "user", "content": [{"text": user_prompt}]},
        ]

        return self.client.invoke_structured(
            messages=messages,
            system=self.system_prompt,
            temperature=self.client.config.bedrock_temperature_analysis,
        )

    def _synthesise(
        self, artifact_text: str, dimension_results: dict[str, dict]
    ) -> dict:
        user_prompt = self.synthesis_prompt.format(
            dimension_results_json=json.dumps(dimension_results, indent=2),
            artifact_text=artifact_text,
        )

        messages = [
            {"role": "user", "content": [{"text": user_prompt}]},
        ]

        return self.client.invoke_structured(
            messages=messages,
            system=self.system_prompt,
            temperature=self.client.config.bedrock_temperature_analysis,
            max_tokens=8192,
        )

    def _build_result(
        self,
        synthesis: dict,
        dimension_results: dict[str, dict],
        iteration_number: int,
    ) -> AnalysisResult:
        dimensions: list[DimensionScore] = []
        for dim_info in synthesis.get("dimension_scores", []):
            dimensions.append(
                DimensionScore(
                    name=dim_info.get("name", ""),
                    score=dim_info.get("score", 0),
                    findings=dim_info.get("top_findings", []),
                    severity=dim_info.get("severity", "INFO"),
                )
            )

        if not dimensions:
            dimensions = self._dimensions_from_raw(dimension_results)

        issues: list[Issue] = []
        for issue_data in synthesis.get("critical_issues", []):
            issues.append(
                Issue(
                    id=issue_data.get("id", "ISSUE-???"),
                    dimension=issue_data.get("dimension", ""),
                    severity=issue_data.get("severity", "WARNING"),
                    description=issue_data.get("description", ""),
                    location=issue_data.get("location", ""),
                    recommendation=issue_data.get("recommendation", ""),
                )
            )

        suggestions: list[Suggestion] = []
        for sug_data in synthesis.get("suggestions", []):
            suggestions.append(
                Suggestion(
                    id=sug_data.get("id", "SUG-???"),
                    original_text=sug_data.get("original_text", ""),
                    suggested_text=sug_data.get("suggested_text", ""),
                    rationale=sug_data.get("rationale", ""),
                )
            )

        return AnalysisResult(
            artifact_type=self.artifact_type,
            overall_score=synthesis.get("overall_score", 0),
            dimensions=dimensions,
            issues=issues,
            suggestions=suggestions,
            iteration_number=iteration_number,
        )

    def _dimensions_from_raw(
        self, dimension_results: dict[str, dict]
    ) -> list[DimensionScore]:
        dimensions: list[DimensionScore] = []
        for name, result in dimension_results.items():
            score = result.get("score", 0)
            if score >= 70:
                severity = "INFO"
            elif score >= 40:
                severity = "WARNING"
            else:
                severity = "CRITICAL"

            findings: list[str] = []
            if summary := result.get("summary"):
                findings.append(summary)

            display_name = self.dimension_display_names.get(name, name)
            dimensions.append(
                DimensionScore(
                    name=display_name,
                    score=score,
                    findings=findings,
                    severity=severity,
                )
            )
        return dimensions
