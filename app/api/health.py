"""Liveness and readiness.

`/health` is the exact contract from the brief (Appendix A.1) and must stay reachable even when
the licence has expired. `/ready` is for us and the host: it also proves the database answers.
"""

import os
from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db import get_engine

router = APIRouter()
STARTED_AT = datetime.now(UTC).isoformat(timespec="seconds")  # changes only if the process restarts


@router.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@router.get("/ready")
def ready() -> JSONResponse:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"ok": False, "error": "DATABASE_UNAVAILABLE"})
    # Render sets RENDER_GIT_COMMIT; evidence files record which commit they tested.
    commit = os.environ.get("RENDER_GIT_COMMIT", "local")[:7]
    return JSONResponse(content={"ok": True, "commit": commit, "started_at": STARTED_AT})
