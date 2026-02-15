"""Iteration engine for the analyse → feedback → revise → re-analyse loop."""

import logging

from ba_analyser.analysers.requirements_analyser import RequirementsAnalyser
from ba_analyser.bedrock_client import BedrockClient
from ba_analyser.models import (
    AnalysisResult,
    ArtifactType,
    ComparisonReport,
    Suggestion,
)

logger = logging.getLogger(__name__)

APPLY_SUGGESTIONS_SYSTEM_PROMPT = """\
You are a precise text editor. Your job is to apply the accepted changes \
to the artifact exactly as specified. Return ONLY the revised artifact text \
with the changes applied. Do not add commentary or explanations."""

APPLY_SUGGESTIONS_USER_PROMPT = """\
<artifact>
{artifact_text}
</artifact>

<accepted_suggestions>
{suggestions_text}
</accepted_suggestions>

<instructions>
Apply each of the accepted suggestions to the artifact above. \
For each suggestion, find the original text and replace it with the \
suggested text. If the original text cannot be found exactly, apply the \
change as closely as possible to the intent.

Return ONLY the revised artifact text with all accepted changes applied. \
Do not wrap in code fences. Do not add any commentary.
</instructions>"""


class IterationEngine:
    """Manages the analyse -> feedback -> revise -> re-analyse loop."""

    def __init__(
        self,
        client: BedrockClient,
        analyser: RequirementsAnalyser | None = None,
    ) -> None:
        self.client = client
        self.analyser = analyser or RequirementsAnalyser(client)
        self.history: list[AnalysisResult] = []
        self._artifact_versions: list[str] = []

    @property
    def current_iteration(self) -> int:
        return len(self.history)

    @property
    def latest_result(self) -> AnalysisResult | None:
        return self.history[-1] if self.history else None

    @property
    def latest_artifact(self) -> str | None:
        return self._artifact_versions[-1] if self._artifact_versions else None

    def analyse(self, artifact_text: str) -> AnalysisResult:
        """Run full analysis and store the result in history."""
        iteration = self.current_iteration + 1
        logger.info("Starting analysis iteration %d", iteration)

        result = self.analyser.analyse(
            artifact_text, iteration_number=iteration
        )

        self.history.append(result)
        self._artifact_versions.append(artifact_text)
        return result

    def get_improvement_suggestions(
        self, result: AnalysisResult | None = None,
    ) -> list[Suggestion]:
        """Return the suggestions from the given (or latest) result."""
        result = result or self.latest_result
        if result is None:
            return []
        return list(result.suggestions)

    def apply_suggestions(
        self,
        artifact_text: str,
        accepted_suggestion_ids: list[str],
    ) -> str:
        """Apply user-accepted suggestions to produce a revised artifact.

        Uses Bedrock to intelligently apply text replacements, handling
        cases where exact matches may not be possible.
        """
        if not self.latest_result:
            return artifact_text

        # Gather accepted suggestions
        accepted = [
            s
            for s in self.latest_result.suggestions
            if s.id in accepted_suggestion_ids
        ]
        if not accepted:
            return artifact_text

        suggestions_text = "\n\n".join(
            f"Suggestion {s.id}:\n"
            f"  Find: {s.original_text}\n"
            f"  Replace with: {s.suggested_text}\n"
            f"  Rationale: {s.rationale}"
            for s in accepted
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": APPLY_SUGGESTIONS_USER_PROMPT.format(
                            artifact_text=artifact_text,
                            suggestions_text=suggestions_text,
                        )
                    }
                ],
            }
        ]

        revised = self.client.invoke(
            messages=messages,
            system=APPLY_SUGGESTIONS_SYSTEM_PROMPT,
            temperature=0.0,
        )

        return revised.strip()

    def compare_iterations(
        self,
        current: int | None = None,
        previous: int | None = None,
    ) -> ComparisonReport:
        """Build a comparison report between two iterations.

        Args:
            current: 1-based iteration number (defaults to latest).
            previous: 1-based iteration number (defaults to current - 1).

        Returns:
            ComparisonReport with deltas and lists of changes.
        """
        if len(self.history) < 2:
            raise ValueError("Need at least 2 iterations to compare.")

        current_idx = (current or self.current_iteration) - 1
        previous_idx = (previous or current_idx) - 1

        if not (0 <= previous_idx < len(self.history)):
            raise ValueError(f"Invalid previous iteration: {previous_idx + 1}")
        if not (0 <= current_idx < len(self.history)):
            raise ValueError(f"Invalid current iteration: {current_idx + 1}")

        curr = self.history[current_idx]
        prev = self.history[previous_idx]

        # Compare dimension scores
        prev_dims = {d.name: d.score for d in prev.dimensions}
        curr_dims = {d.name: d.score for d in curr.dimensions}

        improved = [
            name
            for name in curr_dims
            if curr_dims[name] > prev_dims.get(name, 0)
        ]
        regressed = [
            name
            for name in curr_dims
            if curr_dims[name] < prev_dims.get(name, 100)
        ]

        # Compare issues
        prev_issue_ids = {i.id for i in prev.issues}
        curr_issue_ids = {i.id for i in curr.issues}

        resolved = sorted(prev_issue_ids - curr_issue_ids)
        new_issues = sorted(curr_issue_ids - prev_issue_ids)

        return ComparisonReport(
            previous_iteration=previous_idx + 1,
            current_iteration=current_idx + 1,
            previous_score=prev.overall_score,
            current_score=curr.overall_score,
            score_delta=curr.overall_score - prev.overall_score,
            improved_dimensions=improved,
            regressed_dimensions=regressed,
            resolved_issues=resolved,
            new_issues=new_issues,
        )

    def is_ready(
        self,
        result: AnalysisResult | None = None,
        threshold: float = 80.0,
    ) -> bool:
        """Check if the artifact meets the minimum quality threshold."""
        result = result or self.latest_result
        if result is None:
            return False
        return result.overall_score >= threshold
