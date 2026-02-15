"""Export user stories to multiple formats: Markdown, JSON, CSV."""

import csv
import json
from io import StringIO
from itertools import groupby
from pathlib import Path

from ba_analyser.models import UserStory


def _group_by_epic(stories: list[UserStory]) -> dict[str, list[UserStory]]:
    """Group stories by epic name, preserving order."""
    grouped: dict[str, list[UserStory]] = {}
    for story in stories:
        grouped.setdefault(story.epic, []).append(story)
    return grouped


# ── Markdown ──────────────────────────────────────────────────────────────


def export_markdown(stories: list[UserStory], output_dir: Path) -> Path:
    """Export stories as Markdown story cards, grouped by epic.

    Returns the path to the generated file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "user-stories.md"

    lines: list[str] = ["# User Stories", ""]

    for epic, epic_stories in _group_by_epic(stories).items():
        lines.append(f"## Epic: {epic}")
        lines.append("")

        for story in epic_stories:
            lines.append(f"### {story.id}: {story.title}")
            lines.append("")
            lines.append(
                f"**As a** {story.persona}, "
                f"**I want** {story.goal}, "
                f"**so that** {story.benefit}."
            )
            lines.append("")
            lines.append(
                f"**Priority:** {story.priority} | "
                f"**Complexity:** {story.estimate_complexity}"
            )

            if story.dependencies:
                lines.append(f"**Dependencies:** {', '.join(story.dependencies)}")

            if story.source_requirement_ids:
                lines.append(
                    f"**Source:** {', '.join(story.source_requirement_ids)}"
                )

            lines.append("")
            lines.append("**Acceptance Criteria:**")
            for ac in story.acceptance_criteria:
                lines.append(f"- [ ] {ac}")
            lines.append("")
            lines.append("---")
            lines.append("")

    out_file.write_text("\n".join(lines), encoding="utf-8")
    return out_file


# ── JSON ──────────────────────────────────────────────────────────────────


def export_json(stories: list[UserStory], output_dir: Path) -> Path:
    """Export stories as structured JSON.

    Returns the path to the generated file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "user-stories.json"

    data = {
        "stories": [story.model_dump() for story in stories],
        "epics": list(_group_by_epic(stories).keys()),
        "total_stories": len(stories),
    }

    out_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out_file


# ── CSV ───────────────────────────────────────────────────────────────────


def export_csv(stories: list[UserStory], output_dir: Path) -> Path:
    """Export stories as CSV for import into Jira / Azure DevOps / Trello.

    Returns the path to the generated file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "user-stories.csv"

    headers = [
        "ID",
        "Epic",
        "Title",
        "Story",
        "Persona",
        "Priority",
        "Complexity",
        "Acceptance Criteria",
        "Dependencies",
        "Source Requirements",
    ]

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)

    for story in stories:
        story_text = (
            f"As a {story.persona}, "
            f"I want {story.goal}, "
            f"so that {story.benefit}."
        )
        writer.writerow(
            [
                story.id,
                story.epic,
                story.title,
                story_text,
                story.persona,
                story.priority,
                story.estimate_complexity,
                "\n".join(story.acceptance_criteria),
                ", ".join(story.dependencies),
                ", ".join(story.source_requirement_ids),
            ]
        )

    out_file.write_text(buf.getvalue(), encoding="utf-8")
    return out_file
