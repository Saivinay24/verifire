"""Application factory: wires settings, logging, middleware and routers."""

import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import health, license, routes
from app.config import get_settings
from app.logging_setup import configure_logging, log_event

logger = logging.getLogger("scammap")
STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Community Scam Map", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.allowed_origin],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    # Inner middleware: the licence gate runs on every request (brief: not just at startup).
    app.middleware("http")(license.licence_gate)

    @app.middleware("http")
    async def request_log(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        request_id = uuid.uuid4().hex[:12]
        started = time.perf_counter()
        response: Response = await call_next(request)
        route = request.scope.get("route")
        log_event(
            logger,
            "request",
            request_id=request_id,
            method=request.method,
            # Route template (e.g. /lookup), never the raw URL: query strings carry identifiers.
            route=getattr(route, "path", "unmatched"),
            status=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def bad_request(_: Request, __: RequestValidationError) -> JSONResponse:
        # The brief's contract is 400 for bad input, not FastAPI's default 422. No input echoed back.
        return JSONResponse(status_code=400, content={"error": "invalid request"})

    @app.exception_handler(Exception)
    async def server_error(_: Request, exc: Exception) -> JSONResponse:
        log_event(logger, "unhandled", error=type(exc).__name__)
        return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR"})

    app.include_router(health.router)
    app.include_router(routes.router)
    app.include_router(license.router)

    # The mobile web app: one static shell, served by the same server (no build step).
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifest() -> FileResponse:
        return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")

    return app


app = create_app()
