"""SQLAlchemy Core table definitions mirroring the Alembic migrations (the migrations are the truth)."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

metadata = sa.MetaData()

areas = sa.Table(
    "areas",
    metadata,
    sa.Column("pincode", sa.String(6), primary_key=True),
    sa.Column("locality", sa.Text),
    sa.Column("city", sa.Text),
    sa.Column("lat", sa.Float),
    sa.Column("lng", sa.Float),
)

identifiers = sa.Table(
    "identifiers",
    metadata,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("id_type", sa.String(16)),
    sa.Column("value_norm", sa.Text),
    sa.Column("verified", sa.Boolean),
    sa.Column("verdict", sa.String(24)),
    sa.Column("report_count", sa.Integer),
    sa.Column("distinct_reporters", sa.Integer),
    sa.Column("trust_score", sa.Float),
    sa.Column("campaign_factor", sa.Float),
    sa.Column("unmasked", sa.Boolean),
    sa.Column("first_seen", sa.DateTime(timezone=True)),
    sa.Column("last_seen", sa.DateTime(timezone=True)),
    sa.Column("top_scam_type", sa.Text),
    sa.Column("challenged", sa.Boolean),
    sa.Column("explain", pg.JSONB),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
)

reports = sa.Table(
    "reports",
    metadata,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("report_id", sa.Text),
    sa.Column("identifier_id", sa.BigInteger),
    sa.Column("reporter_key", sa.String(64)),
    sa.Column("ip_key", sa.String(64)),
    sa.Column("occurred_at", sa.DateTime(timezone=True)),
    sa.Column("reported_at", sa.DateTime(timezone=True)),
    sa.Column("received_at", sa.DateTime(timezone=True)),
    sa.Column("channel", sa.Text),
    sa.Column("scam_type", sa.Text),
    sa.Column("pincode", sa.String(6)),
    sa.Column("note_len", sa.Integer),
    sa.Column("note_sig", pg.ARRAY(sa.BigInteger)),
    sa.Column("note_lex", sa.Boolean),
    sa.Column("note_scam", sa.Boolean),
    sa.Column("note_review", sa.Boolean),
    sa.Column("has_screenshot", sa.Boolean),
    sa.Column("amount_lost_inr", sa.BigInteger),
    sa.Column("group_key", sa.Text),
    sa.Column("alert_weight", sa.SmallInteger),
)

challenges = sa.Table(
    "challenges",
    metadata,
    sa.Column("id", sa.Text, primary_key=True),
    sa.Column("identifier_id", sa.BigInteger),
    sa.Column("status", sa.String(16)),
    sa.Column("claimant_name", sa.Text),
    sa.Column("contact_email", sa.Text),
    sa.Column("proof_note", sa.Text),
    sa.Column("created_at", sa.DateTime(timezone=True)),
)

licence_state = sa.Table(
    "licence_state",
    metadata,
    sa.Column("id", sa.SmallInteger, primary_key=True),
    sa.Column("licence", pg.JSONB),
    sa.Column("clock_high_water", sa.DateTime(timezone=True)),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
)
