"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from ba_analyser.cli import app
from ba_analyser.models import (
    AnalysisResult,
    ArtifactType,
    DimensionScore,
    Issue,
    Suggestion,
)

runner = CliRunner()


def _mock_result(score: float = 85.0) -> AnalysisResult:
    return AnalysisResult(
        artifact_type=ArtifactType.REQUIREMENTS_DOCUMENT,
        overall_score=score,
        dimensions=[
            DimensionScore(
                name="Completeness",
                score=80,
                findings=["Good coverage"],
                severity="INFO",
            ),
        ],
        issues=[
            Issue(
                id="ISSUE-001",
                dimension="quality",
                severity="WARNING",
                description="Ambiguous language",
                location="Section 4",
                recommendation="Be more specific",
            ),
        ],
        suggestions=[
            Suggestion(
                id="SUG-001",
                original_text="should be fast",
                suggested_text="shall respond within 2 seconds",
                rationale="Measurable",
            ),
        ],
        iteration_number=1,
    )


@pytest.fixture
def fixture_file(tmp_path) -> Path:
    f = tmp_path / "requirements.md"
    f.write_text("# Requirements\n\nREQ-001: The system shall do things.\n")
    return f


class TestAnalyseCommand:
    @patch("ba_analyser.cli._create_client")
    @patch("ba_analyser.cli.RequirementsAnalyser")
    @patch("ba_analyser.cli.detect_artifact_type")
    def test_analyse_terminal_output(
        self, mock_detect, mock_analyser_cls, mock_create_client, fixture_file
    ):
        mock_detect.return_value = ArtifactType.REQUIREMENTS_DOCUMENT
        mock_analyser = MagicMock()
        mock_analyser.analyse.return_value = _mock_result(score=85)
        mock_analyser_cls.return_value = mock_analyser

        result = runner.invoke(app, ["analyse", str(fixture_file)])

        assert result.exit_code == 0
        assert "85" in result.output

    @patch("ba_analyser.cli._create_client")
    @patch("ba_analyser.cli.RequirementsAnalyser")
    @patch("ba_analyser.cli.detect_artifact_type")
    def test_analyse_json_output(
        self, mock_detect, mock_analyser_cls, mock_create_client, fixture_file
    ):
        mock_detect.return_value = ArtifactType.REQUIREMENTS_DOCUMENT
        mock_analyser = MagicMock()
        mock_analyser.analyse.return_value = _mock_result()
        mock_analyser_cls.return_value = mock_analyser

        result = runner.invoke(
            app, ["analyse", str(fixture_file), "--output", "json"]
        )

        assert result.exit_code == 0
        assert "overall_score" in result.output

    @patch("ba_analyser.cli._create_client")
    @patch("ba_analyser.cli.RequirementsAnalyser")
    @patch("ba_analyser.cli.detect_artifact_type")
    def test_analyse_markdown_output(
        self, mock_detect, mock_analyser_cls, mock_create_client, fixture_file
    ):
        mock_detect.return_value = ArtifactType.REQUIREMENTS_DOCUMENT
        mock_analyser = MagicMock()
        mock_analyser.analyse.return_value = _mock_result()
        mock_analyser_cls.return_value = mock_analyser

        result = runner.invoke(
            app, ["analyse", str(fixture_file), "--output", "markdown"]
        )

        assert result.exit_code == 0
        assert "# Analysis Report" in result.output

    @patch("ba_analyser.cli._create_client")
    @patch("ba_analyser.cli.RequirementsAnalyser")
    @patch("ba_analyser.cli.detect_artifact_type")
    def test_analyse_below_threshold_exits_1(
        self, mock_detect, mock_analyser_cls, mock_create_client, fixture_file
    ):
        mock_detect.return_value = ArtifactType.REQUIREMENTS_DOCUMENT
        mock_analyser = MagicMock()
        mock_analyser.analyse.return_value = _mock_result(score=50)
        mock_analyser_cls.return_value = mock_analyser

        result = runner.invoke(
            app, ["analyse", str(fixture_file), "--threshold", "80"]
        )

        assert result.exit_code == 1
        assert "below" in result.output

    @patch("ba_analyser.cli._create_client")
    @patch("ba_analyser.cli.RequirementsAnalyser")
    def test_analyse_explicit_type_skips_detection(
        self, mock_analyser_cls, mock_create_client, fixture_file
    ):
        mock_analyser = MagicMock()
        mock_analyser.analyse.return_value = _mock_result()
        mock_analyser_cls.return_value = mock_analyser

        result = runner.invoke(
            app, ["analyse", str(fixture_file), "--type", "requirements"]
        )

        assert result.exit_code == 0
        mock_analyser.analyse.assert_called_once()

    def test_analyse_missing_file(self, tmp_path):
        result = runner.invoke(
            app, ["analyse", str(tmp_path / "nonexistent.md")]
        )

        assert result.exit_code == 1

    def test_analyse_empty_file(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        result = runner.invoke(app, ["analyse", str(f)])

        assert result.exit_code == 1
