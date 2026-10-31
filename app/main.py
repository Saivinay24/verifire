"""Application factory: wires settings, logging, middleware and routers."""

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.config import get_settings
from app.logging_setup import configure_logging, log_event

logger = logging.getLogger("scammap")


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

    app.include_router(health.router)
    return app


app = create_app()
