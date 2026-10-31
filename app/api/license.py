"""GET /license and POST /license (brief, "Ship it"), plus the gate every other request passes."""

from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import APIRouter, Body, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.domain.licence import InvalidLicence, Status
from app.services import licence

router = APIRouter()

# Exempt: the two paths the brief names, and the static app shell, which must load to show the
# "Licence expired" screen. Every API call the app makes is still gated.
EXEMPT_EXACT = frozenset({"/health", "/license", "/", "/favicon.ico", "/manifest.webmanifest"})
EXEMPT_PREFIXES = ("/static/",)


@router.get("/license")
def get_license() -> dict[str, Any]:
    return licence.describe()


@router.post("/license")
def post_license(document: Annotated[Any, Body()]) -> Any:
    try:
        return licence.install(document)
    except InvalidLicence as exc:
        return JSONResponse(status_code=400, content={"error": "INVALID_LICENCE", "detail": str(exc)})


async def licence_gate(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    path = request.url.path
    if path in EXEMPT_EXACT or path.startswith(EXEMPT_PREFIXES) or request.method == "OPTIONS":
        return await call_next(request)
    state = await run_in_threadpool(licence.current_status)
    if state is not Status.VALID:
        # Data is locked, never deleted: requests are refused before they reach any handler.
        return JSONResponse(status_code=403, content={"error": "LICENSE_EXPIRED", "reason": state.value})
    return await call_next(request)
