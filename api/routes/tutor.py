"""Read-only tutoring endpoints for the UI, plus thread reset.

GET    /tutor/overview            starter questions and the learning path (static)
GET    /tutor/progress/{id}       concept understanding for one chat thread
DELETE /tutor/session/{id}        forget a thread's history and tutoring state
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import AUTH_ENABLED, require_user_email
from api.routes import session
from src.tutor import engine

router = APIRouter(prefix="/tutor")


def _key(session_id: str, email: str | None) -> str:
    return f"{email}:{session_id}" if email else session_id


@router.get("/overview")
def overview() -> dict:
    return engine.overview()


if AUTH_ENABLED:

    @router.get("/progress/{session_id}")
    def progress(session_id: str, user_email: str = Depends(require_user_email)) -> dict:
        return engine.progress(session.get_tutor_state(_key(session_id, user_email)))

    @router.delete("/session/{session_id}")
    def reset(session_id: str, user_email: str = Depends(require_user_email)) -> dict:
        session.clear(_key(session_id, user_email))
        return {"ok": True}

else:

    @router.get("/progress/{session_id}")
    def progress(session_id: str) -> dict:
        return engine.progress(session.get_tutor_state(_key(session_id, None)))

    @router.delete("/session/{session_id}")
    def reset(session_id: str) -> dict:
        session.clear(_key(session_id, None))
        return {"ok": True}
