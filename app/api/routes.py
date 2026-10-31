"""The seven test-tool endpoints (brief, Appendix A). No login on any of them (rule 5).

Routers only translate HTTP to service calls and errors to the `{"error": ...}` envelope.
"""

import hmac
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Query, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import get_engine
from app.domain.areas import AREAS
from app.domain.identifiers import InvalidIdentifier
from app.repos import store
from app.services import areas, challenges, explore, insights, lookup, report_list, reports

router = APIRouter()


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


def now() -> datetime:
    return datetime.now(UTC)


def _settle_due() -> None:
    """Close disputes past their deadline (throttled to once a minute), then drop stale answers."""
    if challenges.sweep():
        lookup.invalidate()


def _connection_prefix(request: Request) -> str:
    """The /24 (IPv4) or /48 (IPv6) a report came from, for reports sent by our own app.

    The test tool sends ip_prefix itself (brief, rule 2). Only the prefix is kept, and it is hashed
    before storage like every other reporter signal.
    """
    host = request.client.host if request.client else ""
    if ":" in host:
        return ":".join(host.split(":")[:3])
    return ".".join(host.split(".")[:3])


@router.post("/reports", status_code=201)
def post_report(request: Request, payload: Annotated[Any, Body()]) -> Any:
    if not isinstance(payload, dict):
        return error(400, "body must be a JSON object")
    if not payload.get("ip_prefix"):
        payload = {**payload, "ip_prefix": _connection_prefix(request)}
    try:
        accepted = reports.submit(payload, now())
        lookup.invalidate()
    except reports.ReportRejected as exc:
        return error(400, str(exc))
    except reports.RateLimited:
        return error(429, "RATE_LIMITED")
    return {"report_id": accepted.report_id, "case_id": accepted.case_id, "merged": accepted.merged}


@router.get("/lookup")
def get_lookup(type: str = Query(""), value: str = Query("")) -> Any:
    _settle_due()
    try:
        return lookup.lookup(type, value)
    except InvalidIdentifier as exc:
        return error(400, str(exc))


@router.get("/lookup/reports")
def get_lookup_reports(type: str = Query(""), value: str = Query("")) -> Any:
    """Every report filed on one identifier, without who, what they wrote, or how much (extra)."""
    _settle_due()
    try:
        return report_list.reports_filed(type, value)
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
    _settle_due()
    try:
        return areas.area_alerts(pincode, now())
    except areas.UnknownArea as exc:
        return error(400, str(exc))


@router.get("/city")
def get_city(pincode: str = Query(""), days: str | None = None) -> Any:
    """The app's city sheet: hot areas, trending scam types, known scam numbers, a recent feed."""
    _settle_due()
    try:
        d = _positive(days, 7, 90)
    except ValueError:
        return error(400, "days must be a positive number up to 90")
    try:
        return insights.city_pulse(pincode, d, now())
    except areas.UnknownArea as exc:
        return error(400, str(exc))


@router.get("/stats")
def get_stats(days: str | None = None) -> Any:
    """Live numbers across VeriFire, counted after the trust engine."""
    _settle_due()
    try:
        d = _positive(days, 30, 365)
    except ValueError:
        return error(400, "days must be a positive number up to 365")
    return insights.live_stats(d, now())


@router.get("/areas")
def get_areas() -> dict[str, Any]:
    """The supported areas (Appendix B), for the app's area picker and on-device "near me"."""
    return {"areas": [a._asdict() for a in AREAS]}


@router.post("/admin/reset")
def admin_reset() -> dict[str, Any]:
    with get_engine().begin() as conn:
        deleted = store.reset_all(conn)
    lookup.invalidate()
    return {"ok": True, "deleted_reports": deleted}


@router.post("/challenges", status_code=201)
def post_challenge(request: Request, payload: Annotated[Any, Body()]) -> Any:
    if not isinstance(payload, dict):
        return error(400, "body must be a JSON object")
    try:
        result = challenges.challenge(payload, _connection_prefix(request))
        lookup.invalidate()
        return result
    except InvalidIdentifier as exc:
        return error(400, str(exc))
    except challenges.AlreadyReviewed as exc:
        # The last dispute on this number ended against the claim recently; it can't be reopened here.
        return JSONResponse(status_code=409, content={"error": "ALREADY_REVIEWED", "status": exc.status})
    except challenges.TooMany:
        return error(429, "RATE_LIMITED")


# ---- Dispute review (not part of the brief's seven; behind REVIEW_KEY) ----


def _reviewer(request: Request) -> JSONResponse | None:
    key = get_settings().review_key
    if not key:
        return error(404, "reviewing is not switched on")
    given = request.headers.get("x-review-key", "")
    if not hmac.compare_digest(given.encode(), key.encode()):
        return error(401, "wrong review key")
    return None


@router.get("/review/disputes")
def get_review_queue(request: Request, status: str = Query("open")) -> Any:
    if (denied := _reviewer(request)) is not None:
        return denied
    challenges.sweep(force=True)
    return challenges.review_queue(status)


@router.post("/review/disputes/{challenge_id}")
def post_review_decision(request: Request, challenge_id: str, payload: Annotated[Any, Body()]) -> Any:
    if (denied := _reviewer(request)) is not None:
        return denied
    decision = payload.get("decision") if isinstance(payload, dict) else None
    try:
        result = challenges.decide(challenge_id, str(decision))
    except challenges.NotFound as exc:
        return error(400, str(exc))
    lookup.invalidate()
    return result


@router.post("/explore/similar")
def post_similar(payload: Annotated[Any, Body()]) -> Any:
    """Numbers whose reports used close wording to a pasted message. The text is never stored."""
    text = payload.get("text") if isinstance(payload, dict) else None
    if not isinstance(text, str):
        return error(400, "text is required")
    _settle_due()
    try:
        return explore.similar(text, now())
    except explore.TooShort as exc:
        return error(400, str(exc))


@router.get("/explore/known")
def get_known(scam_type: str = Query(""), city: str = Query("")) -> Any:
    _settle_due()
    return explore.known(scam_type or None, city or None, now())
