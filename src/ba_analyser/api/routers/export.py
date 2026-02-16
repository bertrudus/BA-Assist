"""Export router — export stories to various formats."""

import io
import json
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ba_analyser.generators.claude_code_export import ClaudeCodeExporter
from ba_analyser.generators.exporters import export_csv, export_json, export_markdown
from ba_analyser.models import UserStory

router = APIRouter(prefix="/api/export", tags=["export"])


def _stories_from_body(body: dict) -> list[UserStory]:
    """Parse story dicts from request body into UserStory models."""
    return [UserStory(**s) for s in body.get("stories", [])]


@router.post("/markdown")
async def export_md(body: dict):
    stories = _stories_from_body(body)
    if not stories:
        raise HTTPException(400, "No stories provided")

    with tempfile.TemporaryDirectory() as tmpdir:
        out = export_markdown(stories, Path(tmpdir))
        content = out.read_text(encoding="utf-8")

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=user-stories.md"},
    )


@router.post("/json")
async def export_json_route(body: dict):
    stories = _stories_from_body(body)
    if not stories:
        raise HTTPException(400, "No stories provided")

    with tempfile.TemporaryDirectory() as tmpdir:
        out = export_json(stories, Path(tmpdir))
        content = out.read_text(encoding="utf-8")

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=user-stories.json"},
    )


@router.post("/csv")
async def export_csv_route(body: dict):
    stories = _stories_from_body(body)
    if not stories:
        raise HTTPException(400, "No stories provided")

    with tempfile.TemporaryDirectory() as tmpdir:
        out = export_csv(stories, Path(tmpdir))
        content = out.read_text(encoding="utf-8")

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=user-stories.csv"},
    )


@router.post("/claude-code")
async def export_claude_code(body: dict):
    """Export as Claude Code scaffold — returns a ZIP file."""
    stories = _stories_from_body(body)
    artifact_text = body.get("artifact_text", "")
    if not stories:
        raise HTTPException(400, "No stories provided")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "claude-code-project"
        exporter = ClaudeCodeExporter()
        exporter.export(stories, artifact_text, output_dir)

        # Zip the output directory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zf.write(file_path, arcname)
        buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=claude-code-project.zip"},
    )
