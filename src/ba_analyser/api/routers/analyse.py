"""Analyse router — POST /api/analyse (SSE), POST /api/detect-type."""

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ba_analyser.api.dependencies import create_client, get_analyser, get_settings
from ba_analyser.api.schemas import AnalyseRequest, DetectTypeRequest, DetectTypeResponse
from ba_analyser.api.sse import format_sse, run_in_thread
from ba_analyser.detector import detect_artifact_type
from ba_analyser.models import ArtifactType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analyse"])


@router.post("/detect-type")
async def detect_type(req: DetectTypeRequest) -> DetectTypeResponse:
    client = create_client()
    artifact_type = await run_in_thread(detect_artifact_type, req.artifact_text, client)
    return DetectTypeResponse(artifact_type=artifact_type)


@router.post("/analyse")
async def analyse(req: AnalyseRequest):
    """Analyse an artifact with SSE streaming progress."""

    async def event_stream():
        client = create_client()

        # Step 1: Detect type if not provided
        artifact_type = req.artifact_type
        if artifact_type is None:
            yield format_sse("progress", {"step": "detecting_type", "message": "Detecting artifact type..."})
            artifact_type = await run_in_thread(detect_artifact_type, req.artifact_text, client)
            yield format_sse("type_detected", {"artifact_type": artifact_type.value})

        # Step 2: Get analyser and evaluate dimensions with streaming
        analyser = get_analyser(artifact_type, client)
        dimension_results = {}

        for i, dimension_name in enumerate(analyser.dimension_prompts):
            yield format_sse("progress", {
                "step": "evaluating_dimension",
                "dimension": dimension_name,
                "current": i + 1,
                "total": len(analyser.dimension_prompts),
                "message": f"Evaluating {dimension_name}...",
            })

            result = await run_in_thread(
                analyser._evaluate_dimension, req.artifact_text, dimension_name
            )
            dimension_results[dimension_name] = result

            yield format_sse("dimension_complete", {
                "dimension": dimension_name,
                "score": result.get("score", 0),
                "current": i + 1,
                "total": len(analyser.dimension_prompts),
            })

        # Step 3: Synthesise
        yield format_sse("progress", {"step": "synthesising", "message": "Synthesising results..."})
        synthesis = await run_in_thread(
            analyser._synthesise, req.artifact_text, dimension_results
        )

        # Step 4: Build result
        analysis_result = analyser._build_result(synthesis, dimension_results, 1)

        yield format_sse("complete", analysis_result.model_dump())

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
