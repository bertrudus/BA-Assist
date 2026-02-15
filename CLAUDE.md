# BA Artifact Analysis Tool — Claude Code Session Scaffold

## Project Overview

Build an iterative Business Analysis artifact analysis tool that uses **Amazon Bedrock (Claude model)** to review, score, and improve BA deliverables — then convert validated requirements into development-ready user stories for Claude Code.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│                   User Interface (CLI)               │
│         Upload / paste BA artifacts for review       │
├─────────────────────────────────────────────────────┤
│               Artifact Router                        │
│   Detect type: Requirements | Process | User Story   │
├────────────┬────────────┬───────────────────────────┤
│ Requirements│  Process   │   User Story              │
│  Analyser   │  Analyser  │   Analyser                │
├────────────┴────────────┴───────────────────────────┤
│          Amazon Bedrock (Claude Model)               │
│       Prompt chains per artifact type                │
├─────────────────────────────────────────────────────┤
│            Feedback & Iteration Loop                 │
│   Score → Report → Suggest → User revises → Rescore │
├─────────────────────────────────────────────────────┤
│         User Story Generator                         │
│   Requirements → Structured user stories (JSON/MD)   │
├─────────────────────────────────────────────────────┤
│         Claude Code Export                            │
│   Stories → CLAUDE.md / prompt files for dev         │
└─────────────────────────────────────────────────────┘
```

---

## Phase 1 — Project Setup

### Task 1.1: Initialise the project

```
Create a Python project called `ba-analyser` with:
- pyproject.toml (use poetry or pip)
- src/ba_analyser/ package
- tests/ directory
- .env.example for AWS credentials / Bedrock config
- README.md

Dependencies:
- boto3 (Bedrock)
- click or typer (CLI)
- pydantic (data models)
- rich (terminal output / formatting)
- pytest
```

### Task 1.2: Bedrock client wrapper

```
Create src/ba_analyser/bedrock_client.py:
- Wrapper class around boto3 Bedrock Runtime
- Configure for Claude model (e.g. anthropic.claude-3-sonnet or claude-3-5-sonnet)
- Support for:
  - System prompts
  - Structured message chains
  - Temperature control (low for analysis, higher for generation)
  - Token limit management
- Include retry logic and error handling
- Load config from environment variables:
  - AWS_REGION
  - BEDROCK_MODEL_ID
  - MAX_TOKENS
```

---

## Phase 2 — Artifact Type Detection & Data Models

### Task 2.1: Define artifact data models

```
Create src/ba_analyser/models.py using Pydantic:

class ArtifactType(Enum):
    REQUIREMENTS_DOCUMENT
    BUSINESS_PROCESS
    USER_STORY
    USE_CASE
    UNKNOWN

class AnalysisResult:
    artifact_type: ArtifactType
    overall_score: float  # 0-100
    dimensions: list[DimensionScore]
    issues: list[Issue]
    suggestions: list[Suggestion]
    iteration_number: int

class DimensionScore:
    name: str           # e.g. "Completeness", "Consistency"
    score: float        # 0-100
    findings: list[str]
    severity: str       # INFO | WARNING | CRITICAL

class Issue:
    id: str
    dimension: str
    severity: str
    description: str
    location: str       # where in the artifact
    recommendation: str

class Suggestion:
    id: str
    original_text: str
    suggested_text: str
    rationale: str

class UserStory:
    id: str
    epic: str
    title: str
    persona: str
    goal: str
    benefit: str
    acceptance_criteria: list[str]
    priority: str       # MoSCoW
    estimate_complexity: str  # S/M/L/XL
    dependencies: list[str]
    source_requirement_ids: list[str]
```

### Task 2.2: Artifact type detector

```
Create src/ba_analyser/detector.py:
- Function that sends artifact text to Bedrock
- Prompt asks Claude to classify the artifact type
- Returns ArtifactType enum
- Handle ambiguous / mixed artifacts gracefully
```

---

## Phase 3 — Requirements Analyser (Core)

### Task 3.1: Analysis dimensions & prompts

```
Create src/ba_analyser/analysers/requirements_analyser.py:

The analyser must evaluate requirements against these dimensions:

1. COMPLETENESS
   - Are all sections present? (scope, context, stakeholders, functional/non-functional reqs, constraints, assumptions, dependencies, acceptance criteria)
   - Are requirements individually complete? (measurable, testable, traceable)
   - Are edge cases and error scenarios covered?
   - Are non-functional requirements defined (performance, security, scalability, accessibility)?

2. CONSISTENCY
   - Do requirements contradict each other?
   - Is terminology used consistently throughout?
   - Are there duplicate or overlapping requirements?
   - Do priority levels make sense relative to each other?

3. SOLUTION NEUTRALITY
   - Do requirements describe WHAT not HOW?
   - Are there embedded technology/vendor assumptions?
   - Is implementation language used where business language should be?
   - Could the requirement be fulfilled by multiple solutions?

4. CONTEXT & SCOPE CLARITY
   - Is the business problem clearly stated?
   - Are in-scope and out-of-scope items explicit?
   - Are stakeholders and their needs identified?
   - Is the success criteria / definition of done clear?
   - Are assumptions and constraints documented?

5. QUALITY (cross-cutting)
   - Unambiguous language (no "should", "might", "could", "etc.", "and/or")
   - Atomic — one requirement per statement
   - Traceable — each requirement has a unique ID
   - Prioritised — MoSCoW or equivalent
   - Testable — can write a test for each requirement

Build a prompt chain that evaluates each dimension separately,
then synthesises into an overall AnalysisResult.
```

### Task 3.2: Prompt templates

```
Create src/ba_analyser/prompts/ directory with:
- requirements_analysis.py  — system + user prompts per dimension
- process_analysis.py       — for business process artifacts
- user_story_analysis.py    — for existing user stories
- story_generation.py       — for converting reqs → stories

Each prompt file should contain:
- SYSTEM_PROMPT: role and behaviour instructions
- DIMENSION_PROMPTS: dict keyed by dimension name
- SYNTHESIS_PROMPT: combines dimension results into overall score
- OUTPUT_FORMAT: JSON schema the model should return

Use XML tags in prompts for structure.
Keep prompts modular so they can be tuned independently.
```

---

## Phase 4 — Process & User Story Analysers

### Task 4.1: Business process analyser

```
Create src/ba_analyser/analysers/process_analyser.py:

Evaluate business processes for:
- Clear start and end events
- All decision points have defined criteria
- Exception / error paths documented
- Roles and responsibilities assigned to each step
- Handoffs between systems/teams are explicit
- No orphan steps (unreachable or dead-end)
- Process aligns with stated business objectives
```

### Task 4.2: User story analyser

```
Create src/ba_analyser/analysers/story_analyser.py:

Evaluate user stories for:
- Follows "As a [persona], I want [goal], so that [benefit]" format
- Persona is specific (not "user" or "admin" without context)
- Acceptance criteria are testable and complete
- Story is appropriately sized (INVEST principles)
- Dependencies are identified
- No solution language in the story body
- Edge cases covered in acceptance criteria
```

---

## Phase 5 — Iterative Feedback Loop

### Task 5.1: Iteration engine

```
Create src/ba_analyser/iteration.py:

class IterationEngine:
    """Manages the analyse → feedback → revise → re-analyse loop."""

    def __init__(self, bedrock_client, analyser):
        self.history: list[AnalysisResult] = []

    def analyse(self, artifact_text: str) -> AnalysisResult:
        """Run full analysis and store result."""

    def get_improvement_suggestions(self, result: AnalysisResult) -> list[Suggestion]:
        """Generate specific text-level suggestions for each issue."""

    def apply_suggestions(self, artifact_text: str, accepted_suggestions: list[str]) -> str:
        """Apply user-accepted suggestions to produce revised artifact."""

    def compare_iterations(self, current: int, previous: int) -> ComparisonReport:
        """Show what improved / regressed between iterations."""

    def is_ready(self, result: AnalysisResult, threshold: float = 80.0) -> bool:
        """Check if artifact meets minimum quality threshold."""

Workflow:
1. User submits artifact
2. Tool analyses and returns scored report
3. User reviews issues and suggestions
4. User either:
   a. Accepts suggestions (auto-apply)
   b. Manually revises the artifact
   c. Asks for more detail on specific issues
5. Re-submit → re-analyse → compare with previous iteration
6. Repeat until quality threshold met or user is satisfied
7. When ready → proceed to user story generation
```

### Task 5.2: Rich CLI feedback display

```
Create src/ba_analyser/display.py:

Use the `rich` library to display:
- Overall score with colour-coded gauge (red < 40, amber < 70, green >= 70)
- Dimension breakdown table
- Issues list with severity badges
- Suggestions as diff-style before/after
- Iteration comparison (score deltas with arrows ↑↓)
- Progress bar for Bedrock API calls
```

---

## Phase 6 — User Story Generator

### Task 6.1: Requirements to user stories

```
Create src/ba_analyser/generators/story_generator.py:

class StoryGenerator:
    """Converts validated requirements into structured user stories."""

    def generate(self, requirements_text: str, config: GenerationConfig) -> list[UserStory]:
        """
        Prompt chain:
        1. Extract distinct requirements from document
        2. Identify personas from stakeholder/context sections
        3. Group requirements into epics
        4. Generate individual user stories with acceptance criteria
        5. Identify dependencies between stories
        6. Suggest prioritisation (MoSCoW)
        7. Estimate relative complexity
        """

    def refine_story(self, story: UserStory, feedback: str) -> UserStory:
        """Iteratively refine a single story based on user feedback."""

    def validate_coverage(self, requirements_text: str, stories: list[UserStory]) -> CoverageReport:
        """Check all requirements are covered by at least one story."""
```

### Task 6.2: Story output formats

```
Create src/ba_analyser/generators/exporters.py:

Support multiple export formats:

1. Markdown — human-readable story cards
2. JSON — structured data for tool integration
3. Claude Code format — CLAUDE.md and task files:
   - Generate a CLAUDE.md with project context, architecture decisions,
     coding standards, and a backlog of stories
   - Generate individual task prompt files per story/epic
   - Include acceptance criteria as testable requirements
   - Include dependency graph so Claude Code knows build order
4. CSV — for import into Jira / Azure DevOps / Trello
```

---

## Phase 7 — CLI Interface

### Task 7.1: Main CLI

```
Create src/ba_analyser/cli.py using Typer:

Commands:

  ba-analyser analyse <file>
    --type [auto|requirements|process|story]
    --output [terminal|json|markdown]
    --threshold 80
    Analyse a BA artifact and display results.

  ba-analyser iterate <file>
    --threshold 80
    Enter interactive iteration mode.
    Loop: analyse → review → revise → re-analyse.

  ba-analyser generate-stories <file>
    --format [markdown|json|claude-code|csv]
    --output-dir ./output
    Convert requirements into user stories.

  ba-analyser export-claude-code <file>
    --output-dir ./claude-code-project
    Generate full Claude Code scaffolding from requirements:
    - CLAUDE.md
    - Task files per epic/story
    - Architecture notes
    - Dependency order

  ba-analyser compare <file1> <file2>
    Compare two versions of an artifact side-by-side.

  ba-analyser config
    Show / set configuration (model, region, thresholds).
```

---

## Phase 8 — Claude Code Export (The Bridge)

### Task 8.1: Claude Code project generator

```
Create src/ba_analyser/generators/claude_code_export.py:

class ClaudeCodeExporter:
    """Generates a project scaffold that Claude Code can consume."""

    def export(self, stories: list[UserStory], project_context: str) -> None:
        """
        Generates:

        output_dir/
        ├── CLAUDE.md              # Project brief, architecture, standards
        ├── backlog/
        │   ├── epic-1/
        │   │   ├── EPIC.md        # Epic description and goals
        │   │   ├── story-1.md     # Individual story with AC
        │   │   ├── story-2.md
        │   │   └── ...
        │   └── epic-2/
        │       └── ...
        ├── architecture/
        │   └── decisions.md       # Key technical decisions & constraints
        └── iteration-log/
            └── analysis-report.md # Latest analysis scores & notes

        CLAUDE.md should include:
        - Project name and description
        - Business context (from requirements)
        - Architecture guidelines
        - Coding standards
        - Build order (based on story dependencies)
        - Instructions for Claude Code:
          "Work through stories in priority order.
           For each story, implement to satisfy all acceptance criteria.
           Run tests after each story. Commit after each passing story."
        """
```

---

## Phase 9 — Testing

### Task 9.1: Unit tests

```
Create tests/ with:
- test_detector.py      — artifact type classification
- test_requirements.py  — requirements analysis scoring
- test_process.py       — process analysis
- test_stories.py       — user story analysis
- test_generator.py     — story generation & coverage
- test_iteration.py     — iteration comparison logic
- test_exporter.py      — output format correctness

Use sample artifacts in tests/fixtures/:
- good_requirements.md
- bad_requirements.md
- sample_process.md
- sample_stories.md
```

### Task 9.2: Integration tests

```
Create tests/integration/:
- test_bedrock_integration.py  — real Bedrock calls (mark as slow)
- test_end_to_end.py           — full pipeline: analyse → iterate → generate → export
```

---

## Suggested Claude Code Session Order

Work through these in sequence. Each builds on the previous.

```
Step 1:  Project setup & Bedrock client        (Phase 1)
Step 2:  Data models                            (Phase 2)
Step 3:  Prompt templates for requirements      (Phase 3.2)
Step 4:  Requirements analyser                  (Phase 3.1)
Step 5:  CLI — basic `analyse` command          (Phase 7 partial)
Step 6:  Rich display output                    (Phase 5.2)
Step 7:  Iteration engine                       (Phase 5.1)
Step 8:  CLI — `iterate` command                (Phase 7 partial)
Step 9:  Process & story analysers              (Phase 4)
Step 10: Story generator                        (Phase 6.1)
Step 11: Story exporters (MD, JSON, CSV)        (Phase 6.2)
Step 12: Claude Code exporter                   (Phase 8)
Step 13: CLI — remaining commands               (Phase 7 complete)
Step 14: Tests & fixtures                       (Phase 9)
Step 15: README, docs, polish                   (final)
```

---

## Sample Prompt Structure (for reference)

Below is an example of how the requirements completeness prompt might look. Claude Code should use this pattern for all dimension prompts.

```python
COMPLETENESS_SYSTEM_PROMPT = """
You are an expert Business Analyst reviewing a requirements document.
Your task is to evaluate COMPLETENESS only.
You must be thorough, specific, and constructive.
Return your analysis as structured JSON.
"""

COMPLETENESS_USER_PROMPT = """
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the requirements document for COMPLETENESS across these areas:

1. Document structure: Are all expected sections present?
   - Business context / problem statement
   - Scope (in-scope and out-of-scope)
   - Stakeholders
   - Functional requirements
   - Non-functional requirements
   - Constraints and assumptions
   - Dependencies
   - Acceptance criteria / success measures

2. Individual requirement completeness:
   - Is each requirement measurable?
   - Is each requirement testable?
   - Does each have a unique identifier?
   - Are edge cases and error scenarios covered?

3. Coverage gaps:
   - Are there obvious missing requirements given the stated scope?
   - Are non-functional concerns addressed (performance, security, accessibility)?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "completeness",
  "score": <0-100>,
  "missing_sections": ["list of missing sections"],
  "incomplete_requirements": [
    {{
      "requirement_id": "REQ-XXX or description",
      "issue": "what is missing",
      "recommendation": "what to add"
    }}
  ],
  "coverage_gaps": ["list of gaps"],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>
"""
```

---

## Environment Variables

```env
# .env.example
AWS_REGION=eu-west-2
AWS_PROFILE=default
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_MAX_TOKENS=4096
BEDROCK_TEMPERATURE_ANALYSIS=0.1
BEDROCK_TEMPERATURE_GENERATION=0.4
ANALYSIS_QUALITY_THRESHOLD=80
```

---

## Key Design Principles

1. **Separation of concerns** — each analyser is independent and testable
2. **Prompt modularity** — prompts are separate from logic so they can be tuned without code changes
3. **Iterative by default** — the tool assumes multiple passes, not one-shot analysis
4. **Traceability** — every story traces back to source requirements
5. **Claude Code ready** — the final output is designed to be consumed directly by Claude Code
6. **Fail gracefully** — handle Bedrock throttling, malformed responses, and edge cases
