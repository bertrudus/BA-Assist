"""Claude Code project scaffold exporter.

Generates a project structure that Claude Code can consume directly,
including CLAUDE.md, epic/story files, architecture notes, and build order.
"""

from pathlib import Path

from ba_analyser.models import AnalysisResult, UserStory


class ClaudeCodeExporter:
    """Generates a project scaffold that Claude Code can consume."""

    def export(
        self,
        stories: list[UserStory],
        project_context: str,
        output_dir: Path,
        analysis_result: AnalysisResult | None = None,
    ) -> None:
        """Generate the full Claude Code project structure.

        Args:
            stories: Generated user stories.
            project_context: The original requirements text for context.
            output_dir: Root directory to write the scaffold into.
            analysis_result: Optional latest analysis result for the log.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        self._write_claude_md(stories, project_context, output_dir)
        self._write_backlog(stories, output_dir)
        self._write_architecture(project_context, output_dir)

        if analysis_result:
            self._write_iteration_log(analysis_result, output_dir)

    def _write_claude_md(
        self,
        stories: list[UserStory],
        project_context: str,
        output_dir: Path,
    ) -> None:
        """Generate the main CLAUDE.md project file."""
        build_order = self._compute_build_order(stories)
        epics = self._group_by_epic(stories)

        lines = [
            "# Project Brief",
            "",
            "## Business Context",
            "",
        ]

        # Extract first few paragraphs of context as summary
        context_lines = project_context.strip().split("\n")
        summary_lines = context_lines[:20]  # First 20 lines as context
        lines.extend(summary_lines)
        lines.append("")

        # Backlog overview
        lines.append("## Backlog Overview")
        lines.append("")
        lines.append(f"Total stories: {len(stories)}")
        lines.append(f"Epics: {len(epics)}")
        lines.append("")

        for epic_name, epic_stories in epics.items():
            must = sum(1 for s in epic_stories if s.priority == "Must")
            lines.append(
                f"- **{epic_name}** — {len(epic_stories)} stories "
                f"({must} Must-have)"
            )
        lines.append("")

        # Build order
        lines.append("## Build Order")
        lines.append("")
        lines.append(
            "Work through stories in this order (respects dependencies):"
        )
        lines.append("")
        for i, story_id in enumerate(build_order, 1):
            story = next((s for s in stories if s.id == story_id), None)
            if story:
                lines.append(
                    f"{i}. **{story.id}**: {story.title} "
                    f"[{story.priority}, {story.estimate_complexity}]"
                )
        lines.append("")

        # Instructions for Claude Code
        lines.append("## Development Instructions")
        lines.append("")
        lines.append(
            "Work through stories in the build order above. "
            "For each story:"
        )
        lines.append("")
        lines.append(
            "1. Read the story file in `backlog/` for full details"
        )
        lines.append(
            "2. Implement to satisfy all acceptance criteria"
        )
        lines.append("3. Run tests after each story")
        lines.append("4. Commit after each passing story")
        lines.append("")

        (output_dir / "CLAUDE.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )

    def _write_backlog(
        self, stories: list[UserStory], output_dir: Path
    ) -> None:
        """Write epic and story files into backlog/ directory."""
        backlog_dir = output_dir / "backlog"
        epics = self._group_by_epic(stories)

        for epic_idx, (epic_name, epic_stories) in enumerate(
            epics.items(), 1
        ):
            epic_dir = backlog_dir / f"epic-{epic_idx}"
            epic_dir.mkdir(parents=True, exist_ok=True)

            # EPIC.md
            epic_lines = [
                f"# Epic: {epic_name}",
                "",
                f"**Stories:** {len(epic_stories)}",
                "",
                "## Stories in this epic",
                "",
            ]
            for story in epic_stories:
                epic_lines.append(
                    f"- [{story.id}] {story.title} "
                    f"({story.priority}, {story.estimate_complexity})"
                )
            epic_lines.append("")

            (epic_dir / "EPIC.md").write_text(
                "\n".join(epic_lines), encoding="utf-8"
            )

            # Individual story files
            for story in epic_stories:
                story_lines = [
                    f"# {story.id}: {story.title}",
                    "",
                    f"**As a** {story.persona},",
                    f"**I want** {story.goal},",
                    f"**so that** {story.benefit}.",
                    "",
                    f"**Priority:** {story.priority}",
                    f"**Complexity:** {story.estimate_complexity}",
                    f"**Epic:** {story.epic}",
                    "",
                ]

                if story.dependencies:
                    story_lines.append(
                        f"**Dependencies:** {', '.join(story.dependencies)}"
                    )
                    story_lines.append("")

                if story.source_requirement_ids:
                    story_lines.append(
                        f"**Source requirements:** "
                        f"{', '.join(story.source_requirement_ids)}"
                    )
                    story_lines.append("")

                story_lines.append("## Acceptance Criteria")
                story_lines.append("")
                for ac in story.acceptance_criteria:
                    story_lines.append(f"- [ ] {ac}")
                story_lines.append("")

                filename = f"{story.id.lower().replace(' ', '-')}.md"
                (epic_dir / filename).write_text(
                    "\n".join(story_lines), encoding="utf-8"
                )

    def _write_architecture(
        self, project_context: str, output_dir: Path
    ) -> None:
        """Write architecture decisions document."""
        arch_dir = output_dir / "architecture"
        arch_dir.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Architecture Decisions",
            "",
            "## Source Requirements Context",
            "",
            "The following project context was extracted from the "
            "original requirements document:",
            "",
        ]

        # Include constraints, assumptions, dependencies sections if found
        context_lower = project_context.lower()
        for section in [
            "constraints",
            "assumptions",
            "dependencies",
            "non-functional",
        ]:
            start = context_lower.find(section)
            if start != -1:
                # Find the section and include a reasonable chunk
                end = project_context.find("\n#", start + 1)
                if end == -1:
                    end = min(start + 500, len(project_context))
                lines.append(project_context[start:end].strip())
                lines.append("")

        if len(lines) == 7:
            # No sections found, include truncated context
            lines.append(project_context[:1000])
            lines.append("")

        lines.extend(
            [
                "## Technical Decisions",
                "",
                "*(To be documented during implementation)*",
                "",
            ]
        )

        (arch_dir / "decisions.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )

    def _write_iteration_log(
        self, result: AnalysisResult, output_dir: Path
    ) -> None:
        """Write the latest analysis report to iteration-log/."""
        log_dir = output_dir / "iteration-log"
        log_dir.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Analysis Report",
            "",
            f"**Overall Score:** {result.overall_score:.0f}/100",
            f"**Iteration:** {result.iteration_number}",
            f"**Artifact Type:** "
            f"{result.artifact_type.value.replace('_', ' ').title()}",
            "",
            "## Dimension Scores",
            "",
        ]

        for dim in result.dimensions:
            lines.append(f"- **{dim.name}:** {dim.score:.0f}/100 ({dim.severity})")
            for finding in dim.findings:
                lines.append(f"  - {finding}")
        lines.append("")

        if result.issues:
            lines.append("## Outstanding Issues")
            lines.append("")
            for issue in result.issues:
                lines.append(
                    f"- **{issue.id}** [{issue.severity}] "
                    f"{issue.description} — {issue.recommendation}"
                )
            lines.append("")

        (log_dir / "analysis-report.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )

    def _group_by_epic(
        self, stories: list[UserStory]
    ) -> dict[str, list[UserStory]]:
        grouped: dict[str, list[UserStory]] = {}
        for story in stories:
            grouped.setdefault(story.epic, []).append(story)
        return grouped

    def _compute_build_order(self, stories: list[UserStory]) -> list[str]:
        """Topological sort of stories by dependencies.

        Stories with no dependencies come first, then stories whose
        dependencies have already been scheduled. Falls back to
        priority order for stories at the same level.
        """
        priority_rank = {"Must": 0, "Should": 1, "Could": 2, "Won't": 3}
        story_map = {s.id: s for s in stories}
        remaining = set(story_map.keys())
        order: list[str] = []

        while remaining:
            # Find stories whose dependencies are all satisfied
            ready = [
                sid
                for sid in remaining
                if all(
                    dep not in remaining
                    for dep in story_map[sid].dependencies
                )
            ]

            if not ready:
                # Circular dependency — just add remaining in priority order
                ready = sorted(
                    remaining,
                    key=lambda sid: priority_rank.get(
                        story_map[sid].priority, 4
                    ),
                )

            # Sort ready stories by priority then ID
            ready.sort(
                key=lambda sid: (
                    priority_rank.get(story_map[sid].priority, 4),
                    sid,
                )
            )

            for sid in ready:
                order.append(sid)
                remaining.discard(sid)

        return order
