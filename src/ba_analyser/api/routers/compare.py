"""Compare router — analyse two artifacts side-by-side with SSE."""

import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ba_analyser.api.dependencies import create_client
from ba_analyser.api.schemas import CompareRequest
from ba_analyser.api.sse import format_sse, run_in_thread
from ba_analyser.analysers.requirements_analyser import RequirementsAnalyser
from ba_analyser.models import ComparisonReport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["compare"])


@router.post("/compare")
async def compare(req: CompareRequest):
    """Compare two artifacts with SSE streaming."""

    async def event_stream():
        client = create_client()
        analyser = RequirementsAnalyser(client)

        # Analyse first artifact
        yield format_sse("progress", {"step": "analysing_first", "message": "Analysing first artifact..."})

        dimension_results_1 = {}
        for i, dim in enumerate(analyser.dimension_prompts):
            yield format_sse("progress", {
                "step": "evaluating_dimension",
                "artifact": 1,
                "dimension": dim,
                "current": i + 1,
                "total": len(analyser.dimension_prompts),
                "message": f"[1/2] Evaluating {dim}...",
            })
            result = await run_in_thread(analyser._evaluate_dimension, req.artifact_text_1, dim)
            dimension_results_1[dim] = result

        yield format_sse("progress", {"step": "synthesising_first", "message": "Synthesising first artifact..."})
        synthesis_1 = await run_in_thread(analyser._synthesise, req.artifact_text_1, dimension_results_1)
        result_1 = analyser._build_result(synthesis_1, dimension_results_1, 1)
        yield format_sse("artifact_complete", {"artifact": 1, "score": result_1.overall_score})

        # Analyse second artifact
        yield format_sse("progress", {"step": "analysing_second", "message": "Analysing second artifact..."})

        dimension_results_2 = {}
        for i, dim in enumerate(analyser.dimension_prompts):
            yield format_sse("progress", {
                "step": "evaluating_dimension",
                "artifact": 2,
                "dimension": dim,
                "current": i + 1,
                "total": len(analyser.dimension_prompts),
                "message": f"[2/2] Evaluating {dim}...",
            })
            result = await run_in_thread(analyser._evaluate_dimension, req.artifact_text_2, dim)
            dimension_results_2[dim] = result

        yield format_sse("progress", {"step": "synthesising_second", "message": "Synthesising second artifact..."})
        synthesis_2 = await run_in_thread(analyser._synthesise, req.artifact_text_2, dimension_results_2)
        result_2 = analyser._build_result(synthesis_2, dimension_results_2, 2)
        yield format_sse("artifact_complete", {"artifact": 2, "score": result_2.overall_score})

        # Build comparison
        prev_dims = {d.name: d.score for d in result_1.dimensions}
        curr_dims = {d.name: d.score for d in result_2.dimensions}

        improved = [n for n in curr_dims if curr_dims[n] > prev_dims.get(n, 0)]
        regressed = [n for n in curr_dims if curr_dims[n] < prev_dims.get(n, 100)]

        prev_ids = {i.id for i in result_1.issues}
        curr_ids = {i.id for i in result_2.issues}

        comparison = ComparisonReport(
            previous_iteration=1,
            current_iteration=2,
            previous_score=result_1.overall_score,
            current_score=result_2.overall_score,
            score_delta=result_2.overall_score - result_1.overall_score,
            improved_dimensions=improved,
            regressed_dimensions=regressed,
            resolved_issues=sorted(prev_ids - curr_ids),
            new_issues=sorted(curr_ids - prev_ids),
        )

        yield format_sse("complete", {
            "result_1": result_1.model_dump(),
            "result_2": result_2.model_dump(),
            "comparison": comparison.model_dump(),
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
