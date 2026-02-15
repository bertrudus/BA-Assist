"""CLI entrypoint for ba-analyser."""

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ba_analyser.analysers.base import BaseAnalyser
from ba_analyser.analysers.process_analyser import ProcessAnalyser
from ba_analyser.analysers.requirements_analyser import RequirementsAnalyser
from ba_analyser.analysers.story_analyser import StoryAnalyser
from ba_analyser.config import Settings
from ba_analyser.detector import detect_artifact_type
from ba_analyser.display import (
    console as display_console,
    display_comparison,
    display_full_report,
    display_suggestions,
)
from ba_analyser.generators.claude_code_export import ClaudeCodeExporter
from ba_analyser.generators.exporters import export_csv, export_json, export_markdown
from ba_analyser.generators.story_generator import StoryGenerator
from ba_analyser.iteration import IterationEngine
from ba_analyser.models import ArtifactType

app = typer.Typer(
    name="ba-analyser",
    help="Business Analysis artifact analysis tool powered by Amazon Bedrock.",
    no_args_is_help=True,
)

err_console = Console(stderr=True)


class ArtifactTypeOption(str, Enum):
    auto = "auto"
    requirements = "requirements"
    process = "process"
    story = "story"


class OutputFormat(str, Enum):
    terminal = "terminal"
    json = "json"
    markdown = "markdown"


class StoryFormat(str, Enum):
    markdown = "markdown"
    json = "json"
    csv = "csv"
    claude_code = "claude-code"


_TYPE_MAP: dict[ArtifactTypeOption, ArtifactType] = {
    ArtifactTypeOption.requirements: ArtifactType.REQUIREMENTS_DOCUMENT,
    ArtifactTypeOption.process: ArtifactType.BUSINESS_PROCESS,
    ArtifactTypeOption.story: ArtifactType.USER_STORY,
}


def _create_client(settings: Settings):
    """Create the appropriate LLM client based on configuration."""
    if settings.llm_provider == "anthropic":
        from ba_analyser.anthropic_client import AnthropicClient

        return AnthropicClient(config=settings)
    else:
        from ba_analyser.bedrock_client import BedrockClient

        return BedrockClient(config=settings)


def _read_artifact(file: Path) -> str:
    """Read and return the contents of an artifact file."""
    if not file.exists():
        err_console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)
    text = file.read_text(encoding="utf-8")
    if not text.strip():
        err_console.print(f"[red]Error:[/red] File is empty: {file}")
        raise typer.Exit(code=1)
    return text


def _resolve_artifact_type(
    type_option: ArtifactTypeOption,
    artifact_text: str,
    client: BedrockClient,
) -> ArtifactType:
    """Detect or map the artifact type."""
    if type_option != ArtifactTypeOption.auto:
        return _TYPE_MAP[type_option]

    with display_console.status("[bold]Detecting artifact type..."):
        detected = detect_artifact_type(artifact_text, client)

    display_console.print(
        f"Detected artifact type: [bold]{detected.value.replace('_', ' ').title()}[/bold]"
    )
    return detected


def _get_analyser(
    artifact_type: ArtifactType, client: BedrockClient
) -> BaseAnalyser:
    """Return the appropriate analyser for the artifact type."""
    analysers: dict[ArtifactType, type[BaseAnalyser]] = {
        ArtifactType.REQUIREMENTS_DOCUMENT: RequirementsAnalyser,
        ArtifactType.BUSINESS_PROCESS: ProcessAnalyser,
        ArtifactType.USER_STORY: StoryAnalyser,
    }

    analyser_cls = analysers.get(artifact_type)
    if analyser_cls:
        return analyser_cls(client)

    err_console.print(
        f"[yellow]Warning:[/yellow] No specific analyser for "
        f"'{artifact_type.value}'. Falling back to requirements analyser."
    )
    return RequirementsAnalyser(client)


@app.command()
def analyse(
    file: Annotated[
        Path,
        typer.Argument(help="Path to the BA artifact file to analyse."),
    ],
    type: Annotated[
        ArtifactTypeOption,
        typer.Option("--type", "-t", help="Artifact type (auto-detected if not set)."),
    ] = ArtifactTypeOption.auto,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format."),
    ] = OutputFormat.terminal,
    threshold: Annotated[
        float,
        typer.Option("--threshold", help="Minimum quality score to pass."),
    ] = 80.0,
) -> None:
    """Analyse a BA artifact and display results."""
    artifact_text = _read_artifact(file)
    settings = Settings()
    client = _create_client(settings)

    artifact_type = _resolve_artifact_type(type, artifact_text, client)
    analyser = _get_analyser(artifact_type, client)

    with display_console.status("[bold]Analysing artifact..."):
        result = analyser.analyse(artifact_text)

    # Output
    if output == OutputFormat.json:
        display_console.print_json(result.model_dump_json(indent=2))
    elif output == OutputFormat.markdown:
        _print_markdown(result)
    else:
        display_full_report(result)

    # Threshold check
    if result.overall_score < threshold:
        display_console.print(
            f"\n[red]Score {result.overall_score:.0f} is below "
            f"threshold {threshold:.0f}.[/red]"
        )
        raise typer.Exit(code=1)
    else:
        display_console.print(
            f"\n[green]Score {result.overall_score:.0f} meets "
            f"threshold {threshold:.0f}.[/green]"
        )


@app.command()
def iterate(
    file: Annotated[
        Path,
        typer.Argument(help="Path to the BA artifact file to iterate on."),
    ],
    threshold: Annotated[
        float,
        typer.Option("--threshold", help="Target quality score."),
    ] = 80.0,
) -> None:
    """Enter interactive iteration mode: analyse, review, revise, repeat."""
    artifact_text = _read_artifact(file)
    settings = Settings()
    client = _create_client(settings)
    analyser = RequirementsAnalyser(client)
    engine = IterationEngine(client=client, analyser=analyser)

    display_console.print(
        f"\n[bold]Starting iteration mode[/bold] "
        f"(target score: {threshold:.0f})\n"
    )

    while True:
        # Analyse current version
        with display_console.status(
            f"[bold]Analysing (iteration {engine.current_iteration + 1})..."
        ):
            result = engine.analyse(artifact_text)

        display_full_report(result)

        # Show comparison if we have previous iterations
        if engine.current_iteration >= 2:
            comparison = engine.compare_iterations()
            display_console.print()
            display_comparison(comparison)

        # Check threshold
        if engine.is_ready(threshold=threshold):
            display_console.print(
                f"\n[bold green]Score {result.overall_score:.0f} meets "
                f"target {threshold:.0f}. Artifact is ready![/bold green]"
            )
            if Confirm.ask("Save and exit?", default=True):
                _save_artifact(file, artifact_text)
                break

        # Prompt user for next action
        display_console.print()
        action = _prompt_iteration_action(result)

        if action == "accept":
            artifact_text = _handle_accept_suggestions(engine, artifact_text)
        elif action == "revise":
            artifact_text = _handle_manual_revise(file)
        elif action == "detail":
            _handle_show_detail(result)
        elif action == "save":
            _save_artifact(file, artifact_text)
            display_console.print("[green]Artifact saved.[/green]")
        elif action == "quit":
            if engine.current_iteration > 1:
                if Confirm.ask("Save latest version before quitting?"):
                    _save_artifact(file, artifact_text)
            break


@app.command()
def generate_stories(
    file: Annotated[
        Path,
        typer.Argument(help="Path to the requirements file."),
    ],
    format: Annotated[
        StoryFormat,
        typer.Option("--format", "-f", help="Output format."),
    ] = StoryFormat.markdown,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Output directory."),
    ] = Path("./output"),
) -> None:
    """Convert requirements into user stories."""
    artifact_text = _read_artifact(file)
    settings = Settings()
    client = _create_client(settings)
    generator = StoryGenerator(client)

    with display_console.status("[bold]Generating user stories..."):
        stories = generator.generate(artifact_text)

    if not stories:
        err_console.print("[red]No stories were generated.[/red]")
        raise typer.Exit(code=1)

    display_console.print(f"Generated [bold]{len(stories)}[/bold] stories.")

    if format == StoryFormat.claude_code:
        exporter = ClaudeCodeExporter()
        exporter.export(stories, artifact_text, output_dir)
        display_console.print(
            f"[green]Claude Code project exported to {output_dir}[/green]"
        )
    elif format == StoryFormat.json:
        out = export_json(stories, output_dir)
        display_console.print(f"[green]JSON exported to {out}[/green]")
    elif format == StoryFormat.csv:
        out = export_csv(stories, output_dir)
        display_console.print(f"[green]CSV exported to {out}[/green]")
    else:
        out = export_markdown(stories, output_dir)
        display_console.print(f"[green]Markdown exported to {out}[/green]")

    # Validate coverage
    with display_console.status("[bold]Validating requirement coverage..."):
        coverage = generator.validate_coverage(artifact_text, stories)

    display_console.print(
        f"Coverage: [bold]{coverage.coverage_percentage:.0f}%[/bold] "
        f"({coverage.covered_requirements}/{coverage.total_requirements} "
        f"requirements covered)"
    )
    if coverage.uncovered_requirements:
        display_console.print("[yellow]Uncovered requirements:[/yellow]")
        for req_id in coverage.uncovered_requirements:
            display_console.print(f"  - {req_id}")


@app.command()
def export_claude_code(
    file: Annotated[
        Path,
        typer.Argument(help="Path to the requirements file."),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Output directory."),
    ] = Path("./claude-code-project"),
) -> None:
    """Generate full Claude Code scaffolding from requirements."""
    artifact_text = _read_artifact(file)
    settings = Settings()
    client = _create_client(settings)
    generator = StoryGenerator(client)

    # Generate stories
    with display_console.status("[bold]Generating user stories..."):
        stories = generator.generate(artifact_text)

    if not stories:
        err_console.print("[red]No stories were generated.[/red]")
        raise typer.Exit(code=1)

    display_console.print(f"Generated [bold]{len(stories)}[/bold] stories.")

    # Analyse for the iteration log
    analyser = RequirementsAnalyser(client)
    with display_console.status("[bold]Running quality analysis..."):
        analysis = analyser.analyse(artifact_text)

    # Export
    exporter = ClaudeCodeExporter()
    exporter.export(stories, artifact_text, output_dir, analysis_result=analysis)

    display_console.print(
        f"\n[green]Claude Code project exported to {output_dir}/[/green]"
    )
    display_console.print("  CLAUDE.md")
    display_console.print("  backlog/")
    display_console.print("  architecture/")
    display_console.print("  iteration-log/")


@app.command()
def compare(
    file1: Annotated[
        Path,
        typer.Argument(help="Path to the first artifact version."),
    ],
    file2: Annotated[
        Path,
        typer.Argument(help="Path to the second artifact version."),
    ],
) -> None:
    """Compare two versions of an artifact side-by-side."""
    text1 = _read_artifact(file1)
    text2 = _read_artifact(file2)
    settings = Settings()
    client = _create_client(settings)
    analyser = RequirementsAnalyser(client)

    display_console.print(f"[bold]Analysing {file1.name}...[/bold]")
    with display_console.status("[bold]Analysing first version..."):
        result1 = analyser.analyse(text1, iteration_number=1)

    display_console.print(f"[bold]Analysing {file2.name}...[/bold]")
    with display_console.status("[bold]Analysing second version..."):
        result2 = analyser.analyse(text2, iteration_number=2)

    # Build comparison
    prev_dims = {d.name: d.score for d in result1.dimensions}
    curr_dims = {d.name: d.score for d in result2.dimensions}

    improved = [n for n in curr_dims if curr_dims[n] > prev_dims.get(n, 0)]
    regressed = [n for n in curr_dims if curr_dims[n] < prev_dims.get(n, 100)]

    prev_ids = {i.id for i in result1.issues}
    curr_ids = {i.id for i in result2.issues}

    from ba_analyser.models import ComparisonReport

    report = ComparisonReport(
        previous_iteration=1,
        current_iteration=2,
        previous_score=result1.overall_score,
        current_score=result2.overall_score,
        score_delta=result2.overall_score - result1.overall_score,
        improved_dimensions=improved,
        regressed_dimensions=regressed,
        resolved_issues=sorted(prev_ids - curr_ids),
        new_issues=sorted(curr_ids - prev_ids),
    )

    display_console.print(f"\n[bold]{file1.name}[/bold]: {result1.overall_score:.0f}/100")
    display_console.print(f"[bold]{file2.name}[/bold]: {result2.overall_score:.0f}/100")
    display_console.print()
    display_comparison(report)


@app.command()
def config() -> None:
    """Show current configuration."""
    settings = Settings()

    from rich.table import Table

    table = Table(title="Configuration", show_lines=True)
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("LLM Provider", settings.llm_provider)
    if settings.llm_provider == "anthropic":
        table.add_row("Anthropic Model ID", settings.anthropic_model_id)
        table.add_row(
            "Anthropic API Key",
            "***" + settings.anthropic_api_key[-4:]
            if settings.anthropic_api_key
            else "(not set)",
        )
    else:
        table.add_row("AWS Region", settings.aws_region)
        table.add_row("AWS Profile", settings.aws_profile or "(default)")
        table.add_row("Bedrock Model ID", settings.bedrock_model_id)
    table.add_row("Max Tokens", str(settings.bedrock_max_tokens))
    table.add_row("Analysis Temperature", str(settings.bedrock_temperature_analysis))
    table.add_row("Generation Temperature", str(settings.bedrock_temperature_generation))
    table.add_row("Quality Threshold", str(settings.analysis_quality_threshold))

    display_console.print(table)
    display_console.print(
        "\n[dim]Settings are loaded from environment variables and .env file.[/dim]"
    )


def _prompt_iteration_action(result) -> str:
    """Prompt the user for what to do next."""
    choices = {
        "a": "Accept suggestions (auto-apply)",
        "r": "Revise manually (edit file, then re-analyse)",
        "d": "Show detail on specific issues",
        "s": "Save current version",
        "q": "Quit iteration mode",
    }

    display_console.print("[bold]What would you like to do?[/bold]")
    for key, desc in choices.items():
        display_console.print(f"  [bold cyan]{key}[/bold cyan] — {desc}")

    choice = Prompt.ask(
        "Choose",
        choices=list(choices.keys()),
        default="a" if result.suggestions else "r",
    )

    action_map = {"a": "accept", "r": "revise", "d": "detail", "s": "save", "q": "quit"}
    return action_map[choice]


def _handle_accept_suggestions(
    engine: IterationEngine, artifact_text: str
) -> str:
    """Let the user pick which suggestions to accept, then apply them."""
    suggestions = engine.get_improvement_suggestions()
    if not suggestions:
        display_console.print("[yellow]No suggestions available.[/yellow]")
        return artifact_text

    # Show numbered suggestions
    display_console.print("\n[bold]Available suggestions:[/bold]")
    for i, sug in enumerate(suggestions, 1):
        display_console.print(
            f"  [cyan]{i}[/cyan]. [{sug.id}] {sug.rationale}"
        )
        display_console.print(f"      [red]- {sug.original_text}[/red]")
        display_console.print(f"      [green]+ {sug.suggested_text}[/green]")

    selection = Prompt.ask(
        "Accept which suggestions? (e.g. '1,3' or 'all')",
        default="all",
    )

    if selection.strip().lower() == "all":
        accepted_ids = [s.id for s in suggestions]
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            accepted_ids = [
                suggestions[i].id
                for i in indices
                if 0 <= i < len(suggestions)
            ]
        except (ValueError, IndexError):
            display_console.print("[red]Invalid selection. No changes applied.[/red]")
            return artifact_text

    if not accepted_ids:
        display_console.print("[yellow]No suggestions selected.[/yellow]")
        return artifact_text

    display_console.print(
        f"Applying {len(accepted_ids)} suggestion(s)..."
    )
    with display_console.status("[bold]Applying suggestions..."):
        revised = engine.apply_suggestions(artifact_text, accepted_ids)

    display_console.print("[green]Suggestions applied.[/green]")
    return revised


def _handle_manual_revise(file: Path) -> str:
    """Prompt the user to edit the file externally, then reload."""
    display_console.print(
        f"\n[bold]Edit the file and save:[/bold] {file}"
    )
    display_console.print(
        "[dim]Press Enter when you're done editing...[/dim]"
    )
    input()
    return _read_artifact(file)


def _handle_show_detail(result) -> None:
    """Show detailed information about issues."""
    if not result.issues:
        display_console.print("[green]No issues to show.[/green]")
        return

    display_console.print("\n[bold]Issue Details:[/bold]")
    for issue in result.issues:
        display_console.print(
            f"\n[bold]{issue.id}[/bold] "
            f"[{issue.severity}] — {issue.dimension}"
        )
        display_console.print(f"  [bold]Description:[/bold] {issue.description}")
        display_console.print(f"  [bold]Location:[/bold] {issue.location}")
        display_console.print(
            f"  [bold]Recommendation:[/bold] {issue.recommendation}"
        )


def _save_artifact(file: Path, text: str) -> None:
    """Write the artifact text back to the file."""
    file.write_text(text, encoding="utf-8")
    display_console.print(f"[green]Saved to {file}[/green]")


def _print_markdown(result) -> None:
    """Print analysis result in Markdown format."""
    lines = [
        f"# Analysis Report — Iteration {result.iteration_number}",
        f"",
        f"**Artifact type:** {result.artifact_type.value.replace('_', ' ').title()}",
        f"**Overall score:** {result.overall_score:.0f}/100",
        f"",
        f"## Dimension Scores",
        f"",
    ]
    for dim in result.dimensions:
        lines.append(f"### {dim.name} — {dim.score:.0f}/100 ({dim.severity})")
        for f in dim.findings:
            lines.append(f"- {f}")
        lines.append("")

    if result.issues:
        lines.append("## Issues")
        lines.append("")
        for issue in result.issues:
            lines.append(
                f"- **{issue.id}** [{issue.severity}] {issue.description} "
                f"(_{issue.location}_) — {issue.recommendation}"
            )
        lines.append("")

    if result.suggestions:
        lines.append("## Suggestions")
        lines.append("")
        for sug in result.suggestions:
            lines.append(f"### {sug.id}")
            lines.append(f"**Rationale:** {sug.rationale}")
            lines.append(f"```diff")
            lines.append(f"- {sug.original_text}")
            lines.append(f"+ {sug.suggested_text}")
            lines.append(f"```")
            lines.append("")

    display_console.print("\n".join(lines))


if __name__ == "__main__":
    app()
