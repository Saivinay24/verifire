"""The seven test-tool endpoints (brief, Appendix A). No login on any of them (rule 5).

Routers only translate HTTP to service calls and errors to the `{"error": ...}` envelope.
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse

from app.db import get_engine
from app.domain.identifiers import InvalidIdentifier
from app.repos import store
from app.services import areas, challenges, lookup, reports

router = APIRouter()


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


def now() -> datetime:
    return datetime.now(UTC)


@router.post("/reports", status_code=201)
def post_report(payload: Annotated[Any, Body()]) -> Any:
    if not isinstance(payload, dict):
        return error(400, "body must be a JSON object")
    try:
        accepted = reports.submit(payload, now())
    except reports.ReportRejected as exc:
        return error(400, str(exc))
    except reports.RateLimited:
        return error(429, "RATE_LIMITED")
    return {"report_id": accepted.report_id, "case_id": accepted.case_id, "merged": accepted.merged}


@router.get("/lookup")
def get_lookup(type: str = Query(""), value: str = Query("")) -> Any:
    try:
        return lookup.lookup(type, value)
    except InvalidIdentifier as exc:
        return error(400, str(exc))


def _positive(raw: str | None, default: float, limit: float) -> float:
    if raw is None or raw == "":
        return default
    value = float(raw)  # ValueError -> 400 below
    if not 0 < value <= limit:
        raise ValueError
    return value


@router.get("/map")
def get_map(pincode: str = Query(""), days: str | None = None, radius_km: str | None = None) -> Any:
    try:
        d = _positive(days, 7, 365)
        r = _positive(radius_km, 2, 5000)
    except ValueError:
        return error(400, "days and radius_km must be positive numbers")
    try:
        return areas.scam_map(pincode, d, r, now())
    except areas.UnknownArea as exc:
        return error(400, str(exc))


@router.get("/alerts")
def get_alerts(pincode: str = Query("")) -> Any:
    try:
        return areas.area_alerts(pincode, now())
    except areas.UnknownArea as exc:
        return error(400, str(exc))


@router.post("/admin/reset")
def admin_reset() -> dict[str, Any]:
    with get_engine().begin() as conn:
        deleted = store.reset_all(conn)
    return {"ok": True, "deleted_reports": deleted}


@router.post("/challenges", status_code=201)
def post_challenge(payload: Annotated[Any, Body()]) -> Any:
    if not isinstance(payload, dict):
        return error(400, "body must be a JSON object")
    try:
        return challenges.challenge(payload)
    except InvalidIdentifier as exc:
        return error(400, str(exc))
