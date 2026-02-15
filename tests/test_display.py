"""Tests for Rich display functions."""

import re
from io import StringIO

from rich.console import Console


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)

from ba_analyser.display import (
    _score_bar,
    _score_colour,
    display_comparison,
    display_dimensions,
    display_full_report,
    display_issues,
    display_overall_score,
    display_suggestions,
)
from ba_analyser.models import (
    AnalysisResult,
    ArtifactType,
    ComparisonReport,
    DimensionScore,
    Issue,
    Suggestion,
)


def _sample_result(**overrides) -> AnalysisResult:
    defaults = dict(
        artifact_type=ArtifactType.REQUIREMENTS_DOCUMENT,
        overall_score=72.0,
        dimensions=[
            DimensionScore(
                name="Completeness", score=75, findings=["Most sections present"], severity="INFO"
            ),
            DimensionScore(
                name="Quality", score=45, findings=["Ambiguous language found"], severity="WARNING"
            ),
            DimensionScore(
                name="Consistency", score=30, findings=["Contradictions found"], severity="CRITICAL"
            ),
        ],
        issues=[
            Issue(
                id="ISSUE-001",
                dimension="quality",
                severity="CRITICAL",
                description="Vague performance requirement",
                location="Section 5",
                recommendation="Add specific metrics",
            ),
            Issue(
                id="ISSUE-002",
                dimension="completeness",
                severity="WARNING",
                description="Missing non-functional requirements",
                location="Section 5",
                recommendation="Add NFRs",
            ),
            Issue(
                id="ISSUE-003",
                dimension="consistency",
                severity="INFO",
                description="Minor terminology inconsistency",
                location="Section 3",
                recommendation="Standardise terms",
            ),
        ],
        suggestions=[
            Suggestion(
                id="SUG-001",
                original_text="The system should be fast",
                suggested_text="The system shall respond within 2 seconds under normal load",
                rationale="Replace vague language with measurable requirement",
            ),
        ],
        iteration_number=1,
    )
    defaults.update(overrides)
    return AnalysisResult(**defaults)


class TestScoreColour:
    def test_green_for_high_score(self):
        assert _score_colour(85) == "green"

    def test_green_at_boundary(self):
        assert _score_colour(70) == "green"

    def test_yellow_for_medium_score(self):
        assert _score_colour(55) == "yellow"

    def test_yellow_at_boundary(self):
        assert _score_colour(40) == "yellow"

    def test_red_for_low_score(self):
        assert _score_colour(20) == "red"

    def test_red_at_zero(self):
        assert _score_colour(0) == "red"


class TestDisplayFunctions:
    """Verify display functions run without errors and produce output."""

    def _capture(self, func, *args) -> str:
        """Run a display function capturing its output with ANSI stripped."""
        import ba_analyser.display as display_mod

        buf = StringIO()
        original = display_mod.console
        display_mod.console = Console(file=buf, force_terminal=True, width=120)
        try:
            func(*args)
        finally:
            display_mod.console = original
        return _strip_ansi(buf.getvalue())

    def test_display_overall_score(self):
        output = self._capture(display_overall_score, _sample_result())
        assert "72" in output
        assert "Iteration 1" in output

    def test_display_dimensions(self):
        output = self._capture(display_dimensions, _sample_result())
        assert "Completeness" in output
        assert "Quality" in output
        assert "75" in output

    def test_display_dimensions_empty(self):
        output = self._capture(display_dimensions, _sample_result(dimensions=[]))
        assert output == ""

    def test_display_issues(self):
        output = self._capture(display_issues, _sample_result())
        assert "ISSUE-001" in output
        assert "CRITICAL" in output

    def test_display_issues_sorted_by_severity(self):
        output = self._capture(display_issues, _sample_result())
        # CRITICAL should appear before WARNING before INFO
        crit_pos = output.index("ISSUE-001")
        warn_pos = output.index("ISSUE-002")
        info_pos = output.index("ISSUE-003")
        assert crit_pos < warn_pos < info_pos

    def test_display_issues_none(self):
        output = self._capture(display_issues, _sample_result(issues=[]))
        assert "No issues found" in output

    def test_display_suggestions(self):
        output = self._capture(display_suggestions, _sample_result())
        assert "SUG-001" in output
        assert "should be fast" in output
        assert "2 seconds" in output

    def test_display_suggestions_empty(self):
        output = self._capture(display_suggestions, _sample_result(suggestions=[]))
        assert output == ""

    def test_display_full_report(self):
        output = self._capture(display_full_report, _sample_result())
        assert "72" in output
        assert "Completeness" in output
        assert "ISSUE-001" in output

    def test_display_comparison_improved(self):
        report = ComparisonReport(
            previous_iteration=1,
            current_iteration=2,
            previous_score=60,
            current_score=75,
            score_delta=15,
            improved_dimensions=["Completeness", "Quality"],
            regressed_dimensions=[],
            resolved_issues=["ISSUE-001"],
            new_issues=[],
        )
        output = self._capture(display_comparison, report)
        assert "↑" in output
        assert "Improved" in output
        assert "Resolved 1" in output

    def test_display_comparison_regressed(self):
        report = ComparisonReport(
            previous_iteration=1,
            current_iteration=2,
            previous_score=75,
            current_score=60,
            score_delta=-15,
            improved_dimensions=[],
            regressed_dimensions=["Quality"],
            resolved_issues=[],
            new_issues=["ISSUE-005"],
        )
        output = self._capture(display_comparison, report)
        assert "↓" in output
        assert "Regressed" in output
        assert "New 1" in output
