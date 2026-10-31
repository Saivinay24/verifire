"""Structured JSON logging with an allow-list, so personal data can never reach the logs.

Privacy rule 5 of the brief: no personal data in logs. Instead of trying to scrub bad fields,
we only ever emit fields that are explicitly allowed. Anything else passed to the logger is dropped.
"""

import json
import logging
import sys
import time

ALLOWED_FIELDS = frozenset(
    {"event", "request_id", "method", "route", "status", "duration_ms", "rule", "count", "error"}
)


class AllowListJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(record.created)),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        fields = getattr(record, "fields", {})
        payload.update({k: v for k, v in fields.items() if k in ALLOWED_FIELDS})
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(AllowListJsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # Uvicorn's access log prints full URLs including query strings (lookup values). Silence it;
    # our middleware logs the route template instead.
    logging.getLogger("uvicorn.access").disabled = True


def log_event(logger: logging.Logger, msg: str, **fields: object) -> None:
    logger.info(msg, extra={"fields": fields})
