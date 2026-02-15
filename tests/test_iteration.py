"""Tests for the iteration engine."""

from unittest.mock import MagicMock

import pytest

from ba_analyser.iteration import IterationEngine
from ba_analyser.models import (
    AnalysisResult,
    ArtifactType,
    ComparisonReport,
    DimensionScore,
    Issue,
    Suggestion,
)


def _make_result(
    score: float = 70.0,
    iteration: int = 1,
    issues: list[Issue] | None = None,
    suggestions: list[Suggestion] | None = None,
    dimensions: list[DimensionScore] | None = None,
) -> AnalysisResult:
    return AnalysisResult(
        artifact_type=ArtifactType.REQUIREMENTS_DOCUMENT,
        overall_score=score,
        dimensions=dimensions
        or [
            DimensionScore(
                name="Completeness", score=score, findings=["OK"], severity="INFO"
            ),
        ],
        issues=issues or [],
        suggestions=suggestions or [],
        iteration_number=iteration,
    )


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.config.bedrock_temperature_analysis = 0.1
    return client


@pytest.fixture
def mock_analyser():
    return MagicMock()


@pytest.fixture
def engine(mock_client, mock_analyser):
    return IterationEngine(client=mock_client, analyser=mock_analyser)


class TestIterationEngineAnalyse:
    def test_analyse_stores_result_in_history(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result(score=65)

        result = engine.analyse("Some artifact text")

        assert len(engine.history) == 1
        assert engine.history[0].overall_score == 65

    def test_analyse_increments_iteration_number(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result(score=65)

        engine.analyse("Version 1")
        engine.analyse("Version 2")

        assert mock_analyser.analyse.call_count == 2
        # First call: iteration_number=1
        assert mock_analyser.analyse.call_args_list[0].kwargs["iteration_number"] == 1
        # Second call: iteration_number=2
        assert mock_analyser.analyse.call_args_list[1].kwargs["iteration_number"] == 2

    def test_analyse_stores_artifact_versions(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result()

        engine.analyse("Version 1")
        engine.analyse("Version 2")

        assert engine._artifact_versions == ["Version 1", "Version 2"]

    def test_current_iteration_starts_at_zero(self, engine):
        assert engine.current_iteration == 0

    def test_current_iteration_after_analyses(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result()
        engine.analyse("V1")
        engine.analyse("V2")

        assert engine.current_iteration == 2

    def test_latest_result(self, engine, mock_analyser):
        mock_analyser.analyse.side_effect = [
            _make_result(score=50),
            _make_result(score=75),
        ]
        engine.analyse("V1")
        engine.analyse("V2")

        assert engine.latest_result.overall_score == 75

    def test_latest_result_none_when_empty(self, engine):
        assert engine.latest_result is None

    def test_latest_artifact(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result()
        engine.analyse("V1")
        engine.analyse("V2")

        assert engine.latest_artifact == "V2"

    def test_latest_artifact_none_when_empty(self, engine):
        assert engine.latest_artifact is None


class TestIterationEngineComparison:
    def test_compare_iterations_basic(self, engine, mock_analyser):
        mock_analyser.analyse.side_effect = [
            _make_result(
                score=50,
                iteration=1,
                dimensions=[
                    DimensionScore(name="Quality", score=40, findings=[], severity="WARNING"),
                ],
                issues=[
                    Issue(
                        id="ISSUE-001",
                        dimension="quality",
                        severity="WARNING",
                        description="Bad",
                        location="S1",
                        recommendation="Fix",
                    ),
                ],
            ),
            _make_result(
                score=75,
                iteration=2,
                dimensions=[
                    DimensionScore(name="Quality", score=70, findings=[], severity="INFO"),
                ],
                issues=[
                    Issue(
                        id="ISSUE-002",
                        dimension="quality",
                        severity="INFO",
                        description="Minor",
                        location="S2",
                        recommendation="Polish",
                    ),
                ],
            ),
        ]

        engine.analyse("V1")
        engine.analyse("V2")
        report = engine.compare_iterations()

        assert report.previous_iteration == 1
        assert report.current_iteration == 2
        assert report.score_delta == 25
        assert "Quality" in report.improved_dimensions
        assert "ISSUE-001" in report.resolved_issues
        assert "ISSUE-002" in report.new_issues

    def test_compare_iterations_requires_two(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result()
        engine.analyse("V1")

        with pytest.raises(ValueError, match="at least 2"):
            engine.compare_iterations()

    def test_compare_iterations_none_when_empty(self, engine):
        with pytest.raises(ValueError, match="at least 2"):
            engine.compare_iterations()

    def test_compare_specific_iterations(self, engine, mock_analyser):
        mock_analyser.analyse.side_effect = [
            _make_result(score=40, iteration=1),
            _make_result(score=60, iteration=2),
            _make_result(score=80, iteration=3),
        ]
        engine.analyse("V1")
        engine.analyse("V2")
        engine.analyse("V3")

        report = engine.compare_iterations(current=3, previous=1)

        assert report.previous_iteration == 1
        assert report.current_iteration == 3
        assert report.score_delta == 40


class TestIterationEngineIsReady:
    def test_is_ready_above_threshold(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result(score=85)
        engine.analyse("V1")

        assert engine.is_ready(threshold=80) is True

    def test_is_ready_below_threshold(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result(score=60)
        engine.analyse("V1")

        assert engine.is_ready(threshold=80) is False

    def test_is_ready_at_threshold(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result(score=80)
        engine.analyse("V1")

        assert engine.is_ready(threshold=80) is True

    def test_is_ready_no_results(self, engine):
        assert engine.is_ready() is False

    def test_is_ready_with_explicit_result(self, engine):
        result = _make_result(score=90)
        assert engine.is_ready(result=result, threshold=80) is True


class TestIterationEngineSuggestions:
    def test_get_improvement_suggestions_from_latest(self, engine, mock_analyser):
        suggestions = [
            Suggestion(
                id="SUG-001",
                original_text="old",
                suggested_text="new",
                rationale="better",
            ),
        ]
        mock_analyser.analyse.return_value = _make_result(suggestions=suggestions)
        engine.analyse("V1")

        result = engine.get_improvement_suggestions()

        assert len(result) == 1
        assert result[0].id == "SUG-001"

    def test_get_improvement_suggestions_empty(self, engine):
        assert engine.get_improvement_suggestions() == []

    def test_apply_suggestions_calls_bedrock(self, engine, mock_analyser, mock_client):
        suggestions = [
            Suggestion(
                id="SUG-001",
                original_text="should be fast",
                suggested_text="shall respond within 2 seconds",
                rationale="Measurable",
            ),
        ]
        mock_analyser.analyse.return_value = _make_result(suggestions=suggestions)
        engine.analyse("The system should be fast.")

        mock_client.invoke.return_value = "The system shall respond within 2 seconds."

        revised = engine.apply_suggestions(
            "The system should be fast.", ["SUG-001"]
        )

        assert revised == "The system shall respond within 2 seconds."
        mock_client.invoke.assert_called_once()

    def test_apply_suggestions_no_match_returns_original(self, engine, mock_analyser):
        mock_analyser.analyse.return_value = _make_result(suggestions=[])
        engine.analyse("V1")

        result = engine.apply_suggestions("Original text", ["SUG-999"])

        assert result == "Original text"

    def test_apply_suggestions_no_history_returns_original(self, engine):
        result = engine.apply_suggestions("Original text", ["SUG-001"])

        assert result == "Original text"
