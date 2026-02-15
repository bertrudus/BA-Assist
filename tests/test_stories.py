"""Tests for user story analyser."""

from unittest.mock import MagicMock

import pytest

from ba_analyser.analysers.story_analyser import StoryAnalyser
from ba_analyser.models import ArtifactType


def _make_dimension_result(dimension: str, score: float) -> dict:
    return {
        "dimension": dimension,
        "score": score,
        "strengths": ["Good"],
        "summary": f"{dimension} is adequate.",
    }


def _make_synthesis_result(overall_score: float = 78.0) -> dict:
    return {
        "overall_score": overall_score,
        "executive_summary": "Stories are well-written overall.",
        "dimension_scores": [
            {
                "name": "Format Compliance",
                "score": 90,
                "severity": "INFO",
                "top_findings": ["All stories follow format"],
            },
            {
                "name": "Persona Quality",
                "score": 75,
                "severity": "INFO",
                "top_findings": ["Personas are specific"],
            },
            {
                "name": "Acceptance Criteria",
                "score": 70,
                "severity": "INFO",
                "top_findings": ["Most criteria testable"],
            },
            {
                "name": "INVEST Principles",
                "score": 72,
                "severity": "INFO",
                "top_findings": ["Stories are independent"],
            },
        ],
        "critical_issues": [],
        "suggestions": [
            {
                "id": "SUG-001",
                "original_text": "user can do things",
                "suggested_text": "authenticated customer can browse catalogue",
                "rationale": "More specific persona and action",
            },
        ],
    }


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.config.bedrock_temperature_analysis = 0.1
    return client


@pytest.fixture
def analyser(mock_client):
    return StoryAnalyser(mock_client)


class TestStoryAnalyser:
    def test_artifact_type(self, analyser):
        assert analyser.artifact_type == ArtifactType.USER_STORY

    def test_has_four_dimensions(self, analyser):
        assert len(analyser.dimension_prompts) == 4
        assert "format_compliance" in analyser.dimension_prompts
        assert "persona_quality" in analyser.dimension_prompts
        assert "acceptance_criteria" in analyser.dimension_prompts
        assert "invest_principles" in analyser.dimension_prompts

    def test_analyse_calls_all_dimensions_plus_synthesis(
        self, analyser, mock_client
    ):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("format_compliance", 90),
            _make_dimension_result("persona_quality", 75),
            _make_dimension_result("acceptance_criteria", 70),
            _make_dimension_result("invest_principles", 72),
            _make_synthesis_result(),
        ]

        result = analyser.analyse("As a user, I want...")

        assert mock_client.invoke_structured.call_count == 5

    def test_analyse_returns_correct_type(self, analyser, mock_client):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("format_compliance", 90),
            _make_dimension_result("persona_quality", 75),
            _make_dimension_result("acceptance_criteria", 70),
            _make_dimension_result("invest_principles", 72),
            _make_synthesis_result(overall_score=78),
        ]

        result = analyser.analyse("As a user, I want...")

        assert result.artifact_type == ArtifactType.USER_STORY
        assert result.overall_score == 78
        assert len(result.dimensions) == 4
        assert len(result.suggestions) == 1
