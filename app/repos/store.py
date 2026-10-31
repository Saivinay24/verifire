"""Queries. Every function takes an open connection (the service owns the transaction) and does SQL only."""

from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Connection, RowMapping
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.repos.tables import challenges, identifiers, reports


def find_report(conn: Connection, report_id: str) -> RowMapping | None:
    return conn.execute(sa.select(reports).where(reports.c.report_id == report_id)).mappings().first()


def lock_identifier(conn: Connection, id_type: str, value_norm: str, verified: bool) -> RowMapping:
    """Get-or-create the identifier row and lock it, so concurrent reports on one identifier serialise."""
    conn.execute(
        pg_insert(identifiers)
        .values(id_type=id_type, value_norm=value_norm, verified=verified)
        .on_conflict_do_nothing(index_elements=["id_type", "value_norm"])
    )
    row = (
        conn.execute(
            sa.select(identifiers)
            .where(identifiers.c.id_type == id_type, identifiers.c.value_norm == value_norm)
            .with_for_update()
        )
        .mappings()
        .one()
    )
    return row


def identifier_by_id(conn: Connection, identifier_id: int) -> RowMapping:
    return conn.execute(sa.select(identifiers).where(identifiers.c.id == identifier_id)).mappings().one()


def get_identifier(conn: Connection, id_type: str, value_norm: str) -> RowMapping | None:
    return (
        conn.execute(
            sa.select(identifiers).where(
                identifiers.c.id_type == id_type, identifiers.c.value_norm == value_norm
            )
        )
        .mappings()
        .first()
    )


def count_reporter_reports(
    conn: Connection, reporter_key: str, since: datetime, until: datetime, identifier_id: int | None = None
) -> int:
    q = sa.select(sa.func.count()).where(
        reports.c.reporter_key == reporter_key,
        reports.c.reported_at > since,
        reports.c.reported_at <= until,
    )
    if identifier_id is not None:
        q = q.where(reports.c.identifier_id == identifier_id)
    return int(conn.execute(q).scalar_one())


def count_identifier_reports(conn: Connection, identifier_id: int) -> int:
    q = sa.select(sa.func.count()).where(reports.c.identifier_id == identifier_id)
    return int(conn.execute(q).scalar_one())


def insert_report(conn: Connection, values: dict[str, Any]) -> None:
    conn.execute(sa.insert(reports).values(**values))


def identifier_reports(conn: Connection, identifier_id: int) -> Sequence[RowMapping]:
    return (
        conn.execute(
            sa.select(reports).where(reports.c.identifier_id == identifier_id).order_by(reports.c.id)
        )
        .mappings()
        .all()
    )


def reporter_hourly_counts(conn: Connection, identifier_id: int) -> dict[str, int]:
    """Per reporter of this identifier: their reports (any identifier) in the hour up to their latest one."""
    rows = conn.execute(
        sa.text(
            """
            SELECT r.reporter_key, count(*) AS n
            FROM reports r
            JOIN (SELECT reporter_key, max(reported_at) AS t
                  FROM reports WHERE identifier_id = :id GROUP BY reporter_key) x
              ON r.reporter_key = x.reporter_key
             AND r.reported_at > x.t - interval '1 hour' AND r.reported_at <= x.t
            GROUP BY r.reporter_key
            """
        ),
        {"id": identifier_id},
    )
    return {row.reporter_key: int(row.n) for row in rows}


def reporters_of_verified(conn: Connection, reporter_keys: Iterable[str]) -> set[str]:
    keys = list(reporter_keys)
    if not keys:
        return set()
    rows = conn.execute(
        sa.select(reports.c.reporter_key)
        .distinct()
        .join(identifiers, identifiers.c.id == reports.c.identifier_id)
        .where(identifiers.c.verified, reports.c.reporter_key.in_(keys))
    )
    return {row.reporter_key for row in rows}


def update_report_trust(conn: Connection, changes: list[dict[str, Any]]) -> None:
    if not changes:
        return
    conn.execute(
        sa.update(reports)
        .where(reports.c.id == sa.bindparam("rid"))
        .values(group_key=sa.bindparam("g"), alert_weight=sa.bindparam("w")),
        changes,
    )


def update_identifier(conn: Connection, identifier_id: int, values: dict[str, Any]) -> None:
    conn.execute(
        sa.update(identifiers)
        .where(identifiers.c.id == identifier_id)
        .values(**values, updated_at=sa.func.now())
    )


def recent_evidence(
    conn: Connection, identifier_id: int, limit: int, after: datetime | None = None
) -> Sequence[RowMapping]:
    where = [reports.c.identifier_id == identifier_id]
    if after is not None:  # Reports set aside by an upheld review are not evidence any more.
        where.append(reports.c.received_at > after)
    return (
        conn.execute(
            sa.select(reports.c.occurred_at, reports.c.channel, reports.c.scam_type, reports.c.pincode)
            .where(*where)
            .order_by(reports.c.occurred_at.desc())
            .limit(limit)
        )
        .mappings()
        .all()
    )


def filed_reports(
    conn: Connection, identifier_id: int, limit: int, after: datetime | None = None
) -> Sequence[RowMapping]:
    """Every report on one identifier for the "all reports" list. Never the reporter, IP, note or amount."""
    where = [reports.c.identifier_id == identifier_id]
    if after is not None:  # Reports set aside by an upheld review are not shown any more.
        where.append(reports.c.received_at > after)
    return (
        conn.execute(
            sa.select(
                reports.c.occurred_at,
                reports.c.channel,
                reports.c.scam_type,
                reports.c.pincode,
                reports.c.note_len,
                reports.c.has_screenshot,
                (sa.func.coalesce(reports.c.amount_lost_inr, 0) > 0).label("lost_money"),
            )
            .where(*where)
            .order_by(reports.c.occurred_at.desc(), reports.c.id.desc())
            .limit(limit)
        )
        .mappings()
        .all()
    )


def open_challenge(conn: Connection, identifier_id: int) -> RowMapping | None:
    return (
        conn.execute(
            sa.select(challenges).where(
                challenges.c.identifier_id == identifier_id, challenges.c.status == "under_review"
            )
        )
        .mappings()
        .first()
    )


def insert_challenge(conn: Connection, values: dict[str, Any], window: timedelta) -> None:
    conn.execute(
        sa.insert(challenges).values(**values, created_at=sa.func.now(), closes_at=sa.func.now() + window)
    )


def last_closed_challenge(conn: Connection, identifier_id: int) -> RowMapping | None:
    return (
        conn.execute(
            sa.select(challenges)
            .where(challenges.c.identifier_id == identifier_id, challenges.c.status != "under_review")
            .order_by(challenges.c.decided_at.desc().nullslast())
        )
        .mappings()
        .first()
    )


def get_challenge(conn: Connection, challenge_id: str) -> RowMapping | None:
    return conn.execute(sa.select(challenges).where(challenges.c.id == challenge_id)).mappings().first()


def close_challenge(conn: Connection, challenge_id: str, status: str) -> None:
    conn.execute(
        sa.update(challenges)
        .where(challenges.c.id == challenge_id)
        .values(status=status, decided_at=sa.func.now())
    )


def count_network_challenges(conn: Connection, ip_key: str, since: timedelta) -> int:
    q = sa.select(sa.func.count()).where(
        challenges.c.ip_key == ip_key, challenges.c.created_at > sa.func.now() - since
    )
    return int(conn.execute(q).scalar_one())


def due_challenges(conn: Connection) -> list[int]:
    """Identifiers whose open dispute has reached its deadline."""
    rows = conn.execute(
        sa.select(challenges.c.identifier_id).where(
            challenges.c.status == "under_review", challenges.c.closes_at <= sa.func.now()
        )
    )
    return [int(r.identifier_id) for r in rows]


def db_now(conn: Connection) -> datetime:
    return conn.execute(sa.select(sa.func.now())).scalar_one()


def clear_reports_before(conn: Connection, identifier_id: int) -> None:
    conn.execute(
        sa.update(identifiers).where(identifiers.c.id == identifier_id).values(cleared_before=sa.func.now())
    )


def review_queue(conn: Connection, statuses: Sequence[str]) -> Sequence[RowMapping]:
    """Disputes with their number's public state, for the reviewer only (never a public endpoint)."""
    return (
        conn.execute(
            sa.select(
                challenges,
                identifiers.c.id_type,
                identifiers.c.value_norm,
                identifiers.c.verdict,
                identifiers.c.report_count,
                identifiers.c.distinct_reporters,
                identifiers.c.top_scam_type,
                identifiers.c.first_seen,
                identifiers.c.last_seen,
                identifiers.c.explain,
            )
            .join(identifiers, identifiers.c.id == challenges.c.identifier_id)
            .where(challenges.c.status.in_(list(statuses)))
            .order_by(challenges.c.created_at.desc())
        )
        .mappings()
        .all()
    )


def claimant_counts(conn: Connection, column: str) -> dict[str, int]:
    """How many different numbers each contact or network has disputed: the bulk-dispute signal."""
    col = challenges.c[column]
    rows = conn.execute(
        sa.select(col, sa.func.count(sa.distinct(challenges.c.identifier_id)))
        .where(col.is_not(None))
        .group_by(col)
    )
    return {r[0]: int(r[1]) for r in rows}


def report_money(conn: Connection, identifier_id: int, after: datetime | None) -> tuple[int, int, list[str]]:
    """Money reported lost, reports with a loss, and areas, for the reviewer's evidence summary."""
    where = [reports.c.identifier_id == identifier_id]
    if after is not None:
        where.append(reports.c.received_at > after)
    rows = conn.execute(sa.select(reports.c.amount_lost_inr, reports.c.pincode).where(*where)).all()
    return (
        sum(int(r.amount_lost_inr or 0) for r in rows),
        sum(1 for r in rows if r.amount_lost_inr),
        sorted({r.pincode for r in rows}),
    )


def area_reports(
    conn: Connection, pincodes: Sequence[str], since: datetime, *, trusted_only: bool
) -> Sequence[RowMapping]:
    """Reports in some areas since a time. Alerts read only the ones trust rules counted."""
    where = [reports.c.pincode.in_(list(pincodes)), reports.c.occurred_at >= since]
    if trusted_only:
        where.append(reports.c.alert_weight > 0)
    cols = (
        reports.c.pincode,
        reports.c.occurred_at,
        reports.c.scam_type,
        reports.c.reporter_key,
        reports.c.ip_key,
    )
    return conn.execute(sa.select(*cols).where(*where)).mappings().all()


def reports_with_identifiers(
    conn: Connection, since: datetime, pincodes: Sequence[str] | None = None
) -> Sequence[RowMapping]:
    """Reports since a time, each with its identifier's public state. Never the reporter or the note."""
    where = [reports.c.occurred_at >= since]
    if pincodes is not None:
        where.append(reports.c.pincode.in_(list(pincodes)))
    cols = (
        reports.c.pincode,
        reports.c.occurred_at,
        reports.c.channel,
        reports.c.scam_type,
        reports.c.amount_lost_inr,
        reports.c.alert_weight,
        reports.c.reporter_key,
        reports.c.ip_key,
        reports.c.identifier_id,
        identifiers.c.id_type,
        identifiers.c.value_norm,
        identifiers.c.verdict,
        identifiers.c.unmasked,
        identifiers.c.verified,
        identifiers.c.challenged,
        identifiers.c.distinct_reporters,
        identifiers.c.top_scam_type,
        identifiers.c.last_seen,
    )
    return (
        conn.execute(
            sa.select(*cols)
            .join(identifiers, identifiers.c.id == reports.c.identifier_id)
            .where(*where)
            .order_by(reports.c.occurred_at.desc())
        )
        .mappings()
        .all()
    )


def area_scam_types_between(conn: Connection, pincode: str, since: datetime, until: datetime) -> set[str]:
    """Scam types seen in an area in a window, from any accepted report (the stricter novelty test)."""
    rows = conn.execute(
        sa.select(reports.c.scam_type)
        .distinct()
        .where(reports.c.pincode == pincode, reports.c.occurred_at >= since, reports.c.occurred_at < until)
    )
    return {row.scam_type for row in rows}


def reset_all(conn: Connection) -> int:
    deleted = conn.execute(sa.delete(reports)).rowcount
    conn.execute(sa.delete(challenges))
    conn.execute(sa.delete(identifiers))
    return int(deleted or 0)


def fingerprinted_reports(conn: Connection, since: datetime) -> Sequence[RowMapping]:
    """Counted reports with a note or message fingerprint, on identifiers people are warned about.

    For wording search. Returns the fingerprint, never the note (it was never stored) and never
    who reported. Reports set aside by an upheld dispute are left out.
    """
    return (
        conn.execute(
            sa.select(
                reports.c.note_sig,
                reports.c.msg_sig,
                reports.c.pincode,
                reports.c.identifier_id,
                identifiers.c.id_type,
                identifiers.c.value_norm,
                identifiers.c.verdict,
                identifiers.c.unmasked,
                identifiers.c.verified,
                identifiers.c.challenged,
                identifiers.c.distinct_reporters,
                identifiers.c.top_scam_type,
                identifiers.c.last_seen,
            )
            .join(identifiers, identifiers.c.id == reports.c.identifier_id)
            .where(
                reports.c.received_at >= since,
                sa.or_(
                    sa.func.cardinality(reports.c.note_sig) > 0,
                    sa.func.cardinality(reports.c.msg_sig) > 0,
                ),
                reports.c.alert_weight > 0,
                identifiers.c.verdict.in_(["KNOWN_SCAM", "SUSPICIOUS"]),
                identifiers.c.verified.is_not(True),
                sa.or_(
                    identifiers.c.cleared_before.is_(None),
                    reports.c.received_at >= identifiers.c.cleared_before,
                ),
            )
        )
        .mappings()
        .all()
    )


def known_scams(conn: Connection, since: datetime) -> Sequence[RowMapping]:
    """Confirmed scams (unmasked, not disputed, not verified) and the pincodes they were reported in."""
    return (
        conn.execute(
            sa.select(
                identifiers.c.id,
                identifiers.c.id_type,
                identifiers.c.value_norm,
                identifiers.c.unmasked,
                identifiers.c.verified,
                identifiers.c.distinct_reporters,
                identifiers.c.top_scam_type,
                identifiers.c.first_seen,
                identifiers.c.last_seen,
                sa.func.array_agg(sa.distinct(reports.c.pincode)).label("pincodes"),
            )
            .join(reports, reports.c.identifier_id == identifiers.c.id)
            .where(
                identifiers.c.verdict == "KNOWN_SCAM",
                identifiers.c.unmasked.is_(True),
                identifiers.c.challenged.is_not(True),
                identifiers.c.verified.is_not(True),
                identifiers.c.last_seen >= since,
                reports.c.alert_weight > 0,
            )
            .group_by(identifiers.c.id)
            .order_by(identifiers.c.last_seen.desc())
        )
        .mappings()
        .all()
    )
