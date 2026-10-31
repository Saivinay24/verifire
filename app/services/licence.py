"""Licence state: checked on every request, renewed without a restart, safe against clock rollback.

The active licence and the clock high-water mark live in the database (one row), so every server
instance agrees and a restart keeps them. Each process caches them for a few seconds, which keeps
the per-request check in memory while a new upload still takes effect within seconds everywhere.
"""

import json
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import sqlalchemy as sa

from app.db import get_engine
from app.domain import licence as L
from app.domain.timefmt import fmt
from app.repos.tables import licence_state

CACHE_SECONDS = 5.0
HIGH_WATER_EVERY = timedelta(seconds=10)
# A long licence shipped with the code so a fresh deploy starts licensed. It is not a secret:
# anyone can read it, nobody can change it without breaking the signature.
BOOTSTRAP_FILE = Path(__file__).resolve().parents[2] / "licences" / "bootstrap.json"


class _State:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.licence: L.Licence | None = None
        self.high_water: datetime | None = None
        self.loaded_at = 0.0


_state = _State()


def _now() -> datetime:
    return datetime.now(UTC)


def _load(conn: sa.Connection) -> None:
    row = conn.execute(sa.select(licence_state).where(licence_state.c.id == 1)).mappings().first()
    document = row["licence"] if row else None
    if document is None and BOOTSTRAP_FILE.exists():
        document = json.loads(BOOTSTRAP_FILE.read_text())
        conn.execute(sa.update(licence_state).where(licence_state.c.id == 1).values(licence=document))
    try:
        _state.licence = L.verify(document) if document is not None else None
    except L.InvalidLicence:
        _state.licence = None  # A corrupted stored licence locks the server rather than unlocking it.
    _state.high_water = row["clock_high_water"] if row else None
    _state.loaded_at = time.monotonic()


def _advance_high_water(conn: sa.Connection, now: datetime) -> None:
    """Remember the latest time seen. Only moves forward (GREATEST), written at most every 10 s."""
    if _state.high_water is not None and now - _state.high_water < HIGH_WATER_EVERY:
        return
    conn.execute(
        sa.update(licence_state)
        .where(licence_state.c.id == 1)
        .values(
            clock_high_water=sa.func.greatest(sa.func.coalesce(licence_state.c.clock_high_water, now), now)
        )
    )
    _state.high_water = max(now, _state.high_water or now)


def current_status() -> L.Status:
    now = _now()
    with _state.lock:
        if time.monotonic() - _state.loaded_at > CACHE_SECONDS:
            with get_engine().begin() as conn:
                _load(conn)
        result = L.status(_state.licence, now, _state.high_water)
        if result is L.Status.VALID:
            with get_engine().begin() as conn:
                _advance_high_water(conn, now)
        return result


def describe() -> dict[str, Any]:
    result = current_status()
    lic = _state.licence
    if lic is None:
        return {"status": result.value, "licensee": None, "expires_at": None, "seconds_remaining": 0}
    return {
        "status": result.value,
        "licence_id": lic.licence_id,
        "licensee": lic.licensee,
        "issued_at": fmt(lic.issued_at),
        "expires_at": fmt(lic.expires_at),
        "seconds_remaining": max(0, int((lic.expires_at - _now()).total_seconds())),
    }


def install(document: Any) -> dict[str, Any]:
    """Verify and activate a new licence immediately, with no restart. Old data is untouched."""
    lic = L.verify(document)
    now = _now()
    if L.status(lic, now, _state.high_water) is not L.Status.VALID:
        raise L.InvalidLicence("this licence is already expired or dated in the future")
    with _state.lock, get_engine().begin() as conn:
        conn.execute(
            sa.update(licence_state)
            .where(licence_state.c.id == 1)
            .values(licence=lic.raw, updated_at=sa.func.now())
        )
        _state.licence = lic
        _state.loaded_at = time.monotonic()
    return describe()
