# BA Analyser

Business Analysis artifact analysis tool powered by Amazon Bedrock (Claude). Reviews, scores, and improves BA deliverables, then converts validated requirements into development-ready user stories.

## Setup

```bash
poetry install
cp .env.example .env  # Edit with your AWS credentials
```

## Usage

### Analyse a BA artifact

```bash
ba-analyser analyse requirements.md
ba-analyser analyse requirements.md --type requirements --output json
ba-analyser analyse requirements.md --threshold 80
```

Supports artifact types: `auto` (default), `requirements`, `process`, `story`.
Output formats: `terminal` (default), `json`, `markdown`.

### Interactive iteration mode

```bash
ba-analyser iterate requirements.md --threshold 80
```

Analyses the artifact, displays a scored report, then enters an interactive loop where you can accept suggestions, manually revise, or inspect issues. Re-analyses after each change and shows score comparison.

### Generate user stories

```bash
ba-analyser generate-stories requirements.md --format markdown --output-dir ./output
```

Formats: `markdown`, `json`, `csv`, `claude-code`.

### Export as Claude Code project

```bash
ba-analyser export-claude-code requirements.md --output-dir ./claude-code-project
```

Generates a full project scaffold with `CLAUDE.md`, `backlog/` (epics and stories), `architecture/`, and `iteration-log/` — ready for Claude Code to consume.

### Compare two artifact versions

```bash
ba-analyser compare requirements-v1.md requirements-v2.md
```

Analyses both versions and displays a side-by-side comparison with score deltas.

### Show configuration

```bash
ba-analyser config
```

Displays current settings loaded from environment variables and `.env` file.

## Configuration

Settings are loaded from environment variables or a `.env` file. See `.env.example` for all options:

| Variable | Default | Description |
|---|---|---|
| `AWS_REGION` | `eu-west-2` | AWS region for Bedrock |
| `AWS_PROFILE` | `default` | AWS credentials profile |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Bedrock model |
| `BEDROCK_MAX_TOKENS` | `4096` | Max response tokens |
| `BEDROCK_TEMPERATURE_ANALYSIS` | `0.1` | Temperature for analysis |
| `BEDROCK_TEMPERATURE_GENERATION` | `0.4` | Temperature for generation |
| `ANALYSIS_QUALITY_THRESHOLD` | `80` | Default quality threshold |

## Testing

```bash
poetry run pytest -v
```
