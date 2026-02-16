"""Iterate router — session-based analyse/revise loop with SSE."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ba_analyser.api.dependencies import create_client, get_analyser
from ba_analyser.api.schemas import ApplySuggestionsRequest, SessionCreateRequest
from ba_analyser.api.session_manager import sessions
from ba_analyser.api.sse import format_sse, run_in_thread
from ba_analyser.analysers.requirements_analyser import RequirementsAnalyser
from ba_analyser.iteration import IterationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["iterate"])


@router.get("")
def list_sessions():
    return sessions.list_sessions()


@router.post("")
def create_session(req: SessionCreateRequest):
    session = sessions.create(req.artifact_text, req.threshold)
    client = create_client()
    analyser = RequirementsAnalyser(client)
    session.engine = IterationEngine(client=client, analyser=analyser)
    return {"id": session.id, "threshold": session.threshold}


@router.get("/{session_id}")
def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    result = {
        "id": session.id,
        "threshold": session.threshold,
        "iterations": session.engine.current_iteration if session.engine else 0,
        "artifact_text": session.artifact_text,
    }

    if session.engine and session.engine.latest_result:
        result["latest_result"] = session.engine.latest_result.model_dump()

    if session.engine and session.engine.history:
        result["history"] = [
            {"iteration": r.iteration_number, "score": r.overall_score}
            for r in session.engine.history
        ]

    return result


@router.delete("/{session_id}")
def delete_session(session_id: str):
    if not sessions.delete(session_id):
        raise HTTPException(404, "Session not found")
    return {"deleted": True}


@router.post("/{session_id}/analyse")
async def analyse_session(session_id: str):
    """Run analysis on the session's current artifact with SSE streaming."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.engine:
        raise HTTPException(400, "Session not initialised")

    async def event_stream():
        analyser = session.engine.analyser
        artifact_text = session.artifact_text
        iteration = session.engine.current_iteration + 1

        yield format_sse("progress", {
            "step": "starting",
            "iteration": iteration,
            "message": f"Starting iteration {iteration}...",
        })

        # Evaluate dimensions with streaming
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
                analyser._evaluate_dimension, artifact_text, dimension_name
            )
            dimension_results[dimension_name] = result

            yield format_sse("dimension_complete", {
                "dimension": dimension_name,
                "score": result.get("score", 0),
                "current": i + 1,
                "total": len(analyser.dimension_prompts),
            })

        # Synthesise
        yield format_sse("progress", {"step": "synthesising", "message": "Synthesising results..."})
        synthesis = await run_in_thread(
            analyser._synthesise, artifact_text, dimension_results
        )

        # Build result and store in engine
        analysis_result = analyser._build_result(synthesis, dimension_results, iteration)
        session.engine.history.append(analysis_result)
        session.engine._artifact_versions.append(artifact_text)

        response = {"result": analysis_result.model_dump()}

        # Add comparison if we have previous iterations
        if session.engine.current_iteration >= 2:
            comparison = session.engine.compare_iterations()
            response["comparison"] = comparison.model_dump()

        response["is_ready"] = session.engine.is_ready(threshold=session.threshold)

        yield format_sse("complete", response)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{session_id}/suggestions")
def get_suggestions(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.engine:
        raise HTTPException(400, "Session not initialised")

    suggestions = session.engine.get_improvement_suggestions()
    return [s.model_dump() for s in suggestions]


@router.post("/{session_id}/apply-suggestions")
async def apply_suggestions(session_id: str, req: ApplySuggestionsRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.engine:
        raise HTTPException(400, "Session not initialised")

    revised = await run_in_thread(
        session.engine.apply_suggestions,
        session.artifact_text,
        req.accepted_suggestion_ids,
    )
    session.artifact_text = revised
    return {"artifact_text": revised}


@router.put("/{session_id}/artifact")
async def update_artifact(session_id: str, body: dict):
    """Update the session's artifact text (manual revision)."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    session.artifact_text = body.get("artifact_text", session.artifact_text)
    return {"artifact_text": session.artifact_text}
