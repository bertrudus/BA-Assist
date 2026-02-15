"""Tests for story exporters (Markdown, JSON, CSV) and Claude Code exporter."""

import csv
import json
from pathlib import Path

import pytest

from ba_analyser.generators.claude_code_export import ClaudeCodeExporter
from ba_analyser.generators.exporters import export_csv, export_json, export_markdown
from ba_analyser.models import (
    AnalysisResult,
    ArtifactType,
    DimensionScore,
    Issue,
    UserStory,
)


def _sample_stories() -> list[UserStory]:
    return [
        UserStory(
            id="US-001",
            epic="Catalogue",
            title="Browse book catalogue",
            persona="Online Customer",
            goal="browse the book catalogue",
            benefit="discover books to purchase",
            acceptance_criteria=[
                "Books displayed with title, author, price",
                "Pagination with 20 items per page",
            ],
            priority="Must",
            estimate_complexity="M",
            dependencies=[],
            source_requirement_ids=["REQ-F001"],
        ),
        UserStory(
            id="US-002",
            epic="Catalogue",
            title="Search for books",
            persona="Online Customer",
            goal="search for books by title or author",
            benefit="quickly find specific books",
            acceptance_criteria=[
                "Search by title, author, ISBN, keyword",
                "Results within 1 second",
            ],
            priority="Must",
            estimate_complexity="M",
            dependencies=["US-001"],
            source_requirement_ids=["REQ-F002"],
        ),
        UserStory(
            id="US-003",
            epic="Checkout",
            title="Shopping cart",
            persona="Online Customer",
            goal="manage items in a shopping cart",
            benefit="purchase multiple books at once",
            acceptance_criteria=[
                "Add items to cart",
                "Remove items from cart",
                "Update quantities",
            ],
            priority="Must",
            estimate_complexity="L",
            dependencies=["US-001"],
            source_requirement_ids=["REQ-F004"],
        ),
    ]


def _sample_analysis() -> AnalysisResult:
    return AnalysisResult(
        artifact_type=ArtifactType.REQUIREMENTS_DOCUMENT,
        overall_score=72.0,
        dimensions=[
            DimensionScore(
                name="Completeness",
                score=75,
                findings=["Most sections present"],
                severity="INFO",
            ),
        ],
        issues=[
            Issue(
                id="ISSUE-001",
                dimension="quality",
                severity="WARNING",
                description="Vague language",
                location="Section 5",
                recommendation="Be specific",
            ),
        ],
        iteration_number=1,
    )


# ── Markdown exporter ─────────────────────────────────────────────────────


class TestExportMarkdown:
    def test_creates_file(self, tmp_path):
        out = export_markdown(_sample_stories(), tmp_path)

        assert out.exists()
        assert out.name == "user-stories.md"

    def test_contains_story_details(self, tmp_path):
        export_markdown(_sample_stories(), tmp_path)
        content = (tmp_path / "user-stories.md").read_text()

        assert "US-001" in content
        assert "Browse book catalogue" in content
        assert "Online Customer" in content
        assert "Pagination with 20 items per page" in content

    def test_groups_by_epic(self, tmp_path):
        export_markdown(_sample_stories(), tmp_path)
        content = (tmp_path / "user-stories.md").read_text()

        assert "## Epic: Catalogue" in content
        assert "## Epic: Checkout" in content

    def test_includes_dependencies(self, tmp_path):
        export_markdown(_sample_stories(), tmp_path)
        content = (tmp_path / "user-stories.md").read_text()

        assert "US-001" in content  # dependency of US-002

    def test_creates_output_dir(self, tmp_path):
        new_dir = tmp_path / "nested" / "output"
        export_markdown(_sample_stories(), new_dir)

        assert new_dir.exists()


# ── JSON exporter ─────────────────────────────────────────────────────────


class TestExportJson:
    def test_creates_valid_json(self, tmp_path):
        out = export_json(_sample_stories(), tmp_path)

        data = json.loads(out.read_text())
        assert data["total_stories"] == 3
        assert len(data["stories"]) == 3
        assert "Catalogue" in data["epics"]

    def test_story_structure(self, tmp_path):
        export_json(_sample_stories(), tmp_path)
        data = json.loads((tmp_path / "user-stories.json").read_text())

        story = data["stories"][0]
        assert story["id"] == "US-001"
        assert story["persona"] == "Online Customer"
        assert story["priority"] == "Must"
        assert len(story["acceptance_criteria"]) == 2


# ── CSV exporter ──────────────────────────────────────────────────────────


class TestExportCsv:
    def test_creates_csv(self, tmp_path):
        out = export_csv(_sample_stories(), tmp_path)

        assert out.exists()
        assert out.name == "user-stories.csv"

    def test_csv_has_header_and_rows(self, tmp_path):
        export_csv(_sample_stories(), tmp_path)

        with open(tmp_path / "user-stories.csv") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert rows[0][0] == "ID"  # header
        assert len(rows) == 4  # header + 3 stories

    def test_csv_story_data(self, tmp_path):
        export_csv(_sample_stories(), tmp_path)

        with open(tmp_path / "user-stories.csv") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["ID"] == "US-001"
        assert rows[0]["Epic"] == "Catalogue"
        assert rows[0]["Priority"] == "Must"


# ── Claude Code exporter ──────────────────────────────────────────────────


class TestClaudeCodeExporter:
    def test_creates_directory_structure(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(
            _sample_stories(),
            "# Requirements\n\nSome context.",
            tmp_path,
            analysis_result=_sample_analysis(),
        )

        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "backlog").is_dir()
        assert (tmp_path / "architecture").is_dir()
        assert (tmp_path / "iteration-log").is_dir()

    def test_claude_md_content(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(
            _sample_stories(),
            "# Requirements\n\nOnline bookstore project.",
            tmp_path,
        )

        content = (tmp_path / "CLAUDE.md").read_text()
        assert "Build Order" in content
        assert "US-001" in content
        assert "Development Instructions" in content

    def test_backlog_has_epics(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(_sample_stories(), "Context", tmp_path)

        # Two epics: Catalogue and Checkout
        assert (tmp_path / "backlog" / "epic-1" / "EPIC.md").exists()
        assert (tmp_path / "backlog" / "epic-2" / "EPIC.md").exists()

    def test_backlog_has_story_files(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(_sample_stories(), "Context", tmp_path)

        epic1_dir = tmp_path / "backlog" / "epic-1"
        story_files = [f for f in epic1_dir.iterdir() if f.name != "EPIC.md"]
        assert len(story_files) == 2  # US-001, US-002

    def test_story_file_content(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(_sample_stories(), "Context", tmp_path)

        story_file = tmp_path / "backlog" / "epic-1" / "us-001.md"
        content = story_file.read_text()
        assert "Browse book catalogue" in content
        assert "Acceptance Criteria" in content
        assert "Pagination" in content

    def test_architecture_file(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(
            _sample_stories(),
            "# Reqs\n## Constraints\n- Budget: 150k\n## Assumptions\n- API stable",
            tmp_path,
        )

        content = (tmp_path / "architecture" / "decisions.md").read_text()
        assert "Architecture Decisions" in content

    def test_iteration_log(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(
            _sample_stories(),
            "Context",
            tmp_path,
            analysis_result=_sample_analysis(),
        )

        content = (tmp_path / "iteration-log" / "analysis-report.md").read_text()
        assert "72" in content
        assert "ISSUE-001" in content

    def test_no_iteration_log_without_result(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(_sample_stories(), "Context", tmp_path)

        assert not (tmp_path / "iteration-log").exists()

    def test_build_order_respects_dependencies(self, tmp_path):
        exporter = ClaudeCodeExporter()
        exporter.export(_sample_stories(), "Context", tmp_path)

        content = (tmp_path / "CLAUDE.md").read_text()
        # US-001 has no deps, should come before US-002 and US-003
        us001_pos = content.index("US-001")
        us002_pos = content.index("US-002")
        us003_pos = content.index("US-003")
        assert us001_pos < us002_pos
        assert us001_pos < us003_pos
