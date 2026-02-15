"""Rich terminal display for analysis results."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ba_analyser.models import AnalysisResult, ComparisonReport

console = Console()


def _score_colour(score: float) -> str:
    """Return a Rich colour name based on score thresholds."""
    if score >= 70:
        return "green"
    if score >= 40:
        return "yellow"
    return "red"


def _severity_style(severity: str) -> str:
    """Return a Rich style string for a severity level."""
    return {
        "CRITICAL": "bold red",
        "WARNING": "bold yellow",
        "INFO": "bold cyan",
    }.get(severity, "white")


def _score_bar(score: float, width: int = 20) -> Text:
    """Build a coloured bar representing a 0-100 score."""
    filled = round(score / 100 * width)
    empty = width - filled
    colour = _score_colour(score)
    bar = Text()
    bar.append("█" * filled, style=colour)
    bar.append("░" * empty, style="dim")
    bar.append(f" {score:.0f}", style=f"bold {colour}")
    return bar


# ── Overall score ──────────────────────────────────────────────────────────


def display_overall_score(result: AnalysisResult) -> None:
    """Display the overall score as a large colour-coded panel."""
    colour = _score_colour(result.overall_score)
    score_text = Text(f"{result.overall_score:.0f}/100", style=f"bold {colour}")

    panel = Panel(
        score_text,
        title=f"[bold]Overall Score — Iteration {result.iteration_number}[/bold]",
        subtitle=f"[dim]{result.artifact_type.value.replace('_', ' ').title()}[/dim]",
        border_style=colour,
        padding=(1, 4),
    )
    console.print(panel)


# ── Dimension breakdown ───────────────────────────────────────────────────


def display_dimensions(result: AnalysisResult) -> None:
    """Display dimension scores in a table with bar charts."""
    if not result.dimensions:
        return

    table = Table(title="Dimension Breakdown", show_lines=True)
    table.add_column("Dimension", style="bold", min_width=22)
    table.add_column("Score", justify="center", min_width=26)
    table.add_column("Severity", justify="center", min_width=10)
    table.add_column("Key Findings", min_width=30)

    for dim in result.dimensions:
        findings_text = "\n".join(f"• {f}" for f in dim.findings[:3])
        table.add_row(
            dim.name,
            _score_bar(dim.score),
            Text(dim.severity, style=_severity_style(dim.severity)),
            findings_text or "[dim]No findings[/dim]",
        )

    console.print(table)


# ── Issues ────────────────────────────────────────────────────────────────


def display_issues(result: AnalysisResult) -> None:
    """Display issues grouped by severity."""
    if not result.issues:
        console.print("[green]No issues found.[/green]")
        return

    table = Table(title="Issues", show_lines=True)
    table.add_column("ID", style="dim", min_width=10)
    table.add_column("Severity", justify="center", min_width=10)
    table.add_column("Dimension", min_width=14)
    table.add_column("Description", min_width=30)
    table.add_column("Location", min_width=12)
    table.add_column("Recommendation", min_width=30)

    # Sort: CRITICAL first, then WARNING, then INFO
    severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    sorted_issues = sorted(
        result.issues, key=lambda i: severity_order.get(i.severity, 3)
    )

    for issue in sorted_issues:
        table.add_row(
            issue.id,
            Text(issue.severity, style=_severity_style(issue.severity)),
            issue.dimension,
            issue.description,
            issue.location,
            issue.recommendation,
        )

    console.print(table)


# ── Suggestions ───────────────────────────────────────────────────────────


def display_suggestions(result: AnalysisResult) -> None:
    """Display suggestions as diff-style before/after panels."""
    if not result.suggestions:
        return

    console.print("\n[bold]Suggestions[/bold]")
    for sug in result.suggestions:
        console.print(f"\n[dim]{sug.id}[/dim] — {sug.rationale}")
        console.print(Text(f"  - {sug.original_text}", style="red"))
        console.print(Text(f"  + {sug.suggested_text}", style="green"))


# ── Iteration comparison ──────────────────────────────────────────────────


def display_comparison(report: ComparisonReport) -> None:
    """Display comparison between two iterations with deltas."""
    delta = report.score_delta
    arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
    delta_colour = "green" if delta > 0 else "red" if delta < 0 else "yellow"

    header = Text()
    header.append(f"Iteration {report.previous_iteration}", style="dim")
    header.append(" → ", style="white")
    header.append(f"Iteration {report.current_iteration}", style="bold")
    header.append(f"  {arrow} {delta:+.1f}", style=f"bold {delta_colour}")

    panel = Panel(
        header,
        title="[bold]Iteration Comparison[/bold]",
        border_style=delta_colour,
        padding=(0, 2),
    )
    console.print(panel)

    if report.improved_dimensions:
        console.print(
            "[green]Improved:[/green] "
            + ", ".join(report.improved_dimensions)
        )
    if report.regressed_dimensions:
        console.print(
            "[red]Regressed:[/red] "
            + ", ".join(report.regressed_dimensions)
        )
    if report.resolved_issues:
        console.print(
            f"[green]Resolved {len(report.resolved_issues)} issue(s)[/green]"
        )
    if report.new_issues:
        console.print(
            f"[yellow]New {len(report.new_issues)} issue(s)[/yellow]"
        )


# ── Full report ───────────────────────────────────────────────────────────


def display_full_report(result: AnalysisResult) -> None:
    """Display the complete analysis report."""
    console.print()
    display_overall_score(result)
    console.print()
    display_dimensions(result)
    console.print()
    display_issues(result)
    display_suggestions(result)
    console.print()
