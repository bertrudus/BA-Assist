"""In-memory session store for iteration mode."""

import uuid
from dataclasses import dataclass, field

from ba_analyser.iteration import IterationEngine
from ba_analyser.models import AnalysisResult, UserStory


@dataclass
class Session:
    id: str
    artifact_text: str
    threshold: float = 80.0
    engine: IterationEngine | None = None
    stories: list[UserStory] = field(default_factory=list)


class SessionManager:
    """Thread-safe in-memory session store."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, artifact_text: str, threshold: float = 80.0) -> Session:
        session_id = uuid.uuid4().hex[:12]
        session = Session(
            id=session_id,
            artifact_text=artifact_text,
            threshold=threshold,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def list_sessions(self) -> list[dict]:
        return [
            {
                "id": s.id,
                "iterations": s.engine.current_iteration if s.engine else 0,
                "latest_score": (
                    s.engine.latest_result.overall_score
                    if s.engine and s.engine.latest_result
                    else None
                ),
                "threshold": s.threshold,
            }
            for s in self._sessions.values()
        ]


# Singleton
sessions = SessionManager()
