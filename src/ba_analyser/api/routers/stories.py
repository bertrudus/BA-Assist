"""Stories router — generate, refine, and validate coverage with SSE."""

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ba_analyser.api.dependencies import create_client
from ba_analyser.api.schemas import GenerateStoriesRequest, RefineStoryRequest
from ba_analyser.api.session_manager import sessions
from ba_analyser.api.sse import format_sse, run_in_thread
from ba_analyser.generators.story_generator import StoryGenerator
from ba_analyser.models import UserStory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.post("/generate")
async def generate_stories(req: GenerateStoriesRequest):
    """Generate user stories from requirements with SSE streaming."""

    async def event_stream():
        client = create_client()
        generator = StoryGenerator(client)

        # Step 1: Extract requirements
        yield format_sse("progress", {"step": "extracting_requirements", "message": "Extracting requirements..."})
        requirements = await run_in_thread(
            generator._extract_requirements, req.artifact_text
        )
        yield format_sse("step_complete", {"step": "extracting_requirements"})

        # Step 2: Identify personas
        yield format_sse("progress", {"step": "identifying_personas", "message": "Identifying personas..."})
        personas = await run_in_thread(
            generator._identify_personas, req.artifact_text, requirements
        )
        yield format_sse("step_complete", {"step": "identifying_personas"})

        # Step 3: Generate stories
        yield format_sse("progress", {"step": "generating_stories", "message": "Generating user stories..."})
        raw_stories = await run_in_thread(
            generator._generate_stories, req.artifact_text, requirements, personas
        )
        stories = generator._parse_stories(raw_stories)
        yield format_sse("step_complete", {"step": "generating_stories", "count": len(stories)})

        # Step 4: Validate coverage
        yield format_sse("progress", {"step": "validating_coverage", "message": "Validating coverage..."})
        coverage = await run_in_thread(
            generator.validate_coverage, req.artifact_text, stories
        )

        yield format_sse("complete", {
            "stories": [s.model_dump() for s in stories],
            "coverage": coverage.model_dump(),
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/refine")
async def refine_story(req: RefineStoryRequest):
    """Refine a story based on feedback. Expects story data in session."""
    # For simplicity, the frontend sends the full story data along with feedback
    raise HTTPException(501, "Use /api/sessions/{id}/stories/{story_id}/refine for session-based refinement")


@router.post("/generate-and-store/{session_id}")
async def generate_and_store(session_id: str):
    """Generate stories for a session's artifact and store them in the session."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    async def event_stream():
        client = create_client()
        generator = StoryGenerator(client)

        yield format_sse("progress", {"step": "extracting_requirements", "message": "Extracting requirements..."})
        requirements = await run_in_thread(
            generator._extract_requirements, session.artifact_text
        )
        yield format_sse("step_complete", {"step": "extracting_requirements"})

        yield format_sse("progress", {"step": "identifying_personas", "message": "Identifying personas..."})
        personas = await run_in_thread(
            generator._identify_personas, session.artifact_text, requirements
        )
        yield format_sse("step_complete", {"step": "identifying_personas"})

        yield format_sse("progress", {"step": "generating_stories", "message": "Generating user stories..."})
        raw_stories = await run_in_thread(
            generator._generate_stories, session.artifact_text, requirements, personas
        )
        stories = generator._parse_stories(raw_stories)
        session.stories = stories
        yield format_sse("step_complete", {"step": "generating_stories", "count": len(stories)})

        yield format_sse("progress", {"step": "validating_coverage", "message": "Validating coverage..."})
        coverage = await run_in_thread(
            generator.validate_coverage, session.artifact_text, stories
        )

        yield format_sse("complete", {
            "stories": [s.model_dump() for s in stories],
            "coverage": coverage.model_dump(),
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
