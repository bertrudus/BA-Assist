"""SSE (Server-Sent Events) helpers for streaming progress to the frontend."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Callable
from typing import Any

logger = logging.getLogger(__name__)


def format_sse(event: str, data: Any) -> str:
    """Format a single SSE message."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


async def run_in_thread(func: Callable, *args) -> Any:
    """Run a blocking function in a thread executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
