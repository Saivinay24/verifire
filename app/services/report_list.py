"""All reports filed on one identifier (extra, not in Appendix A).

Shows only what lookup's evidence already shows (when, how, what, which area), plus three yes/no
proof badges. Never who reported, their IP, what they wrote, or how much they lost. Notes are not
stored, so they cannot be shown. Times are rounded to the hour, like the city feed.
"""

from typing import Any

from app.db import get_engine
from app.domain.areas import AREAS_BY_PINCODE
from app.domain.constants import NOTE_SHORT_CHARS
from app.domain.identifiers import normalise, parse_type
from app.domain.timefmt import IST, fmt
from app.domain.trust import Verdict
from app.repos import store
from app.services import lookup

LIST_LIMIT = 200


def reports_filed(raw_type: str, raw_value: str) -> dict[str, Any]:
    id_type = parse_type(raw_type)
    value = normalise(id_type, raw_value)  # InvalidIdentifier -> 400 at the API layer
    answer = lookup.lookup(raw_type, raw_value)
    head = {
        "verdict": answer["verdict"],
        "display_value": answer["display_value"],
        "report_count": answer["report_count"],
        "distinct_reporters": answer["distinct_reporters"],
        "challenged": answer["challenged"],
    }
    # Official numbers answer from the official list; reports never change them, so none are listed.
    if answer["verdict"] == Verdict.VERIFIED_BUSINESS.value or not answer["report_count"]:
        return {**head, "shown": 0, "reports": []}
    with get_engine().connect() as conn:
        row = store.get_identifier(conn, id_type, value)
        rows = store.filed_reports(conn, row["id"], LIST_LIMIT, after=row["cleared_before"]) if row else []
    items = []
    for r in rows:
        area = AREAS_BY_PINCODE.get(r["pincode"])
        items.append(
            {
                "occurred_at": fmt(
                    r["occurred_at"].astimezone(IST).replace(minute=0, second=0, microsecond=0)
                ),
                "channel": r["channel"],
                "scam_type": r["scam_type"],
                "pincode": r["pincode"],
                "locality": area.locality if area else None,
                "city": area.city if area else None,
                "screenshot": bool(r["has_screenshot"]),
                "lost_money": bool(r["lost_money"]),
                "described": (r["note_len"] or 0) >= NOTE_SHORT_CHARS,
            }
        )
    return {**head, "shown": len(items), "reports": items}
