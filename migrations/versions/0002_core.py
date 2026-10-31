"""Core tables: identifiers (verdict cache), reports, challenges, licence state.

Privacy by design: reports hold keyed hashes of reporter_id and ip_prefix and a MinHash
signature of the note. Raw reporter_id, ip_prefix and note text are never stored.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "identifiers",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("id_type", sa.String(16), nullable=False),
        sa.Column("value_norm", sa.Text, nullable=False),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("verdict", sa.String(24), nullable=False, server_default="NO_REPORTS"),
        sa.Column("report_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("distinct_reporters", sa.Integer, nullable=False, server_default="0"),
        sa.Column("trust_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("campaign_factor", sa.Float, nullable=False, server_default="1"),
        sa.Column("unmasked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("first_seen", sa.DateTime(timezone=True)),
        sa.Column("last_seen", sa.DateTime(timezone=True)),
        sa.Column("top_scam_type", sa.Text),
        sa.Column("challenged", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("explain", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("id_type", "value_norm", name="uq_identifier"),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("report_id", sa.Text, nullable=False, unique=True),
        sa.Column("identifier_id", sa.BigInteger, sa.ForeignKey("identifiers.id"), nullable=False),
        sa.Column("reporter_key", sa.String(64), nullable=False),
        sa.Column("ip_key", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("channel", sa.Text, nullable=False),
        sa.Column("scam_type", sa.Text, nullable=False),
        sa.Column("pincode", sa.String(6), sa.ForeignKey("areas.pincode"), nullable=False),
        sa.Column("note_len", sa.Integer, nullable=False),
        sa.Column("note_sig", pg.ARRAY(sa.BigInteger), nullable=False),
        sa.Column("note_lex", sa.Boolean, nullable=False),
        sa.Column("has_screenshot", sa.Boolean, nullable=False),
        sa.Column("amount_lost_inr", sa.BigInteger, nullable=False),
        sa.Column("group_key", sa.Text),
        sa.Column("alert_weight", sa.SmallInteger, nullable=False, server_default="0"),
    )
    op.create_index("ix_reports_identifier_time", "reports", ["identifier_id", "reported_at"])
    op.create_index("ix_reports_reporter_time", "reports", ["reporter_key", "reported_at"])
    op.create_index(
        "ix_reports_area_trusted",
        "reports",
        ["pincode", "occurred_at"],
        postgresql_where=sa.text("alert_weight > 0"),
    )
    op.create_table(
        "challenges",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("identifier_id", sa.BigInteger, sa.ForeignKey("identifiers.id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        # The claimant is a business asking for review, not a reporter; kept for review only and
        # never returned by any public endpoint or written to logs.
        sa.Column("claimant_name", sa.Text),
        sa.Column("contact_email", sa.Text),
        sa.Column("proof_note", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_challenges_identifier", "challenges", ["identifier_id"])
    op.create_table(
        "licence_state",
        sa.Column("id", sa.SmallInteger, primary_key=True),
        sa.Column("licence", pg.JSONB),
        sa.Column("clock_high_water", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("id = 1", name="ck_licence_singleton"),
    )
    op.execute("INSERT INTO licence_state (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table("licence_state")
    op.drop_table("challenges")
    op.drop_table("reports")
    op.drop_table("identifiers")
