"""Tests for requirements analyser."""

from unittest.mock import MagicMock

import pytest

from ba_analyser.analysers.requirements_analyser import RequirementsAnalyser
from ba_analyser.models import ArtifactType


def _make_dimension_result(dimension: str, score: float) -> dict:
    """Helper to create a mock dimension result."""
    return {
        "dimension": dimension,
        "score": score,
        "strengths": ["Well structured"],
        "summary": f"{dimension} is adequate.",
    }


def _make_synthesis_result(
    overall_score: float = 72.0,
    num_issues: int = 2,
    num_suggestions: int = 1,
) -> dict:
    """Helper to create a mock synthesis result."""
    return {
        "overall_score": overall_score,
        "executive_summary": "The document is generally adequate.",
        "dimension_scores": [
            {
                "name": "Completeness",
                "score": 75,
                "severity": "INFO",
                "top_findings": ["Most sections present"],
            },
            {
                "name": "Consistency",
                "score": 80,
                "severity": "INFO",
                "top_findings": ["Terminology is consistent"],
            },
            {
                "name": "Solution Neutrality",
                "score": 60,
                "severity": "WARNING",
                "top_findings": ["Some technology references"],
            },
            {
                "name": "Context & Scope Clarity",
                "score": 70,
                "severity": "INFO",
                "top_findings": ["Scope is defined"],
            },
            {
                "name": "Quality",
                "score": 65,
                "severity": "WARNING",
                "top_findings": ["Some ambiguous language"],
            },
        ],
        "critical_issues": [
            {
                "id": f"ISSUE-{i:03d}",
                "dimension": "quality",
                "severity": "WARNING",
                "description": f"Issue {i}",
                "location": "Section 4",
                "recommendation": f"Fix issue {i}",
            }
            for i in range(1, num_issues + 1)
        ],
        "suggestions": [
            {
                "id": f"SUG-{i:03d}",
                "original_text": "The system should be fast",
                "suggested_text": "The system shall respond within 2 seconds",
                "rationale": "Measurable requirement",
            }
            for i in range(1, num_suggestions + 1)
        ],
    }


@pytest.fixture
def mock_client():
    client = MagicMock()
    # Set up config attribute for temperature access
    client.config.bedrock_temperature_analysis = 0.1
    return client


@pytest.fixture
def analyser(mock_client):
    return RequirementsAnalyser(mock_client)


class TestRequirementsAnalyser:
    def test_analyse_calls_all_dimensions_plus_synthesis(
        self, analyser, mock_client
    ):
        """analyse() should call Bedrock 6 times: 5 dimensions + 1 synthesis."""
        # First 5 calls return dimension results, 6th returns synthesis
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("completeness", 75),
            _make_dimension_result("consistency", 80),
            _make_dimension_result("solution_neutrality", 60),
            _make_dimension_result("context_scope_clarity", 70),
            _make_dimension_result("quality", 65),
            _make_synthesis_result(),
        ]

        result = analyser.analyse("Some requirements text")

        assert mock_client.invoke_structured.call_count == 6

    def test_analyse_returns_correct_type(self, analyser, mock_client):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("completeness", 75),
            _make_dimension_result("consistency", 80),
            _make_dimension_result("solution_neutrality", 60),
            _make_dimension_result("context_scope_clarity", 70),
            _make_dimension_result("quality", 65),
            _make_synthesis_result(overall_score=72),
        ]

        result = analyser.analyse("Some requirements text")

        assert result.artifact_type == ArtifactType.REQUIREMENTS_DOCUMENT
        assert result.overall_score == 72
        assert result.iteration_number == 1

    def test_analyse_populates_dimensions(self, analyser, mock_client):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("completeness", 75),
            _make_dimension_result("consistency", 80),
            _make_dimension_result("solution_neutrality", 60),
            _make_dimension_result("context_scope_clarity", 70),
            _make_dimension_result("quality", 65),
            _make_synthesis_result(),
        ]

        result = analyser.analyse("Some requirements text")

        assert len(result.dimensions) == 5
        names = {d.name for d in result.dimensions}
        assert "Completeness" in names
        assert "Quality" in names

    def test_analyse_populates_issues(self, analyser, mock_client):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("completeness", 75),
            _make_dimension_result("consistency", 80),
            _make_dimension_result("solution_neutrality", 60),
            _make_dimension_result("context_scope_clarity", 70),
            _make_dimension_result("quality", 65),
            _make_synthesis_result(num_issues=3),
        ]

        result = analyser.analyse("Some requirements text")

        assert len(result.issues) == 3
        assert result.issues[0].id == "ISSUE-001"

    def test_analyse_populates_suggestions(self, analyser, mock_client):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("completeness", 75),
            _make_dimension_result("consistency", 80),
            _make_dimension_result("solution_neutrality", 60),
            _make_dimension_result("context_scope_clarity", 70),
            _make_dimension_result("quality", 65),
            _make_synthesis_result(num_suggestions=2),
        ]

        result = analyser.analyse("Some requirements text")

        assert len(result.suggestions) == 2
        assert result.suggestions[0].original_text == "The system should be fast"

    def test_analyse_respects_iteration_number(self, analyser, mock_client):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("completeness", 75),
            _make_dimension_result("consistency", 80),
            _make_dimension_result("solution_neutrality", 60),
            _make_dimension_result("context_scope_clarity", 70),
            _make_dimension_result("quality", 65),
            _make_synthesis_result(),
        ]

        result = analyser.analyse("Some text", iteration_number=3)

        assert result.iteration_number == 3

    def test_analyse_fallback_when_synthesis_missing_dimension_scores(
        self, analyser, mock_client
    ):
        """If synthesis doesn't return dimension_scores, build from raw."""
        synthesis_no_dims = {
            "overall_score": 70,
            "executive_summary": "OK",
            "dimension_scores": [],
            "critical_issues": [],
            "suggestions": [],
        }
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("completeness", 75),
            _make_dimension_result("consistency", 80),
            _make_dimension_result("solution_neutrality", 60),
            _make_dimension_result("context_scope_clarity", 70),
            _make_dimension_result("quality", 65),
            synthesis_no_dims,
        ]

        result = analyser.analyse("Some text")

        # Should still have 5 dimensions from fallback
        assert len(result.dimensions) == 5
