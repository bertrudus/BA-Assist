"""Tests for process analyser."""

from unittest.mock import MagicMock

import pytest

from ba_analyser.analysers.process_analyser import ProcessAnalyser
from ba_analyser.models import ArtifactType


def _make_dimension_result(dimension: str, score: float) -> dict:
    return {
        "dimension": dimension,
        "score": score,
        "strengths": ["Well structured"],
        "summary": f"{dimension} is adequate.",
    }


def _make_synthesis_result(overall_score: float = 70.0) -> dict:
    return {
        "overall_score": overall_score,
        "executive_summary": "Process is generally adequate.",
        "dimension_scores": [
            {
                "name": "Structure",
                "score": 75,
                "severity": "INFO",
                "top_findings": ["Clear start/end"],
            },
            {
                "name": "Decision Points",
                "score": 65,
                "severity": "WARNING",
                "top_findings": ["Some missing criteria"],
            },
            {
                "name": "Roles & Responsibilities",
                "score": 70,
                "severity": "INFO",
                "top_findings": ["Roles assigned"],
            },
            {
                "name": "Business Alignment",
                "score": 68,
                "severity": "WARNING",
                "top_findings": ["Objective could be clearer"],
            },
        ],
        "critical_issues": [
            {
                "id": "ISSUE-001",
                "dimension": "decision_points",
                "severity": "WARNING",
                "description": "Missing exception path",
                "location": "Step 4",
                "recommendation": "Add error handling",
            },
        ],
        "suggestions": [],
    }


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.config.bedrock_temperature_analysis = 0.1
    return client


@pytest.fixture
def analyser(mock_client):
    return ProcessAnalyser(mock_client)


class TestProcessAnalyser:
    def test_artifact_type(self, analyser):
        assert analyser.artifact_type == ArtifactType.BUSINESS_PROCESS

    def test_has_four_dimensions(self, analyser):
        assert len(analyser.dimension_prompts) == 4
        assert "structure" in analyser.dimension_prompts
        assert "decision_points" in analyser.dimension_prompts
        assert "roles_responsibilities" in analyser.dimension_prompts
        assert "business_alignment" in analyser.dimension_prompts

    def test_analyse_calls_all_dimensions_plus_synthesis(
        self, analyser, mock_client
    ):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("structure", 75),
            _make_dimension_result("decision_points", 65),
            _make_dimension_result("roles_responsibilities", 70),
            _make_dimension_result("business_alignment", 68),
            _make_synthesis_result(),
        ]

        result = analyser.analyse("Some process text")

        # 4 dimensions + 1 synthesis = 5 calls
        assert mock_client.invoke_structured.call_count == 5

    def test_analyse_returns_correct_type(self, analyser, mock_client):
        mock_client.invoke_structured.side_effect = [
            _make_dimension_result("structure", 75),
            _make_dimension_result("decision_points", 65),
            _make_dimension_result("roles_responsibilities", 70),
            _make_dimension_result("business_alignment", 68),
            _make_synthesis_result(overall_score=70),
        ]

        result = analyser.analyse("Some process text")

        assert result.artifact_type == ArtifactType.BUSINESS_PROCESS
        assert result.overall_score == 70
        assert len(result.dimensions) == 4
        assert len(result.issues) == 1
