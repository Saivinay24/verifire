"""Disputes get a lifecycle: a deadline, an outcome, and the signals a reviewer needs.

A dispute used to stay "under review" forever, so anyone (a scammer included) could soften the
warning on a number for good. Now every dispute ends: a reviewer decides, new victims overrule it,
or it lapses at its deadline. See app/services/challenges.py for the rules.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("challenges", sa.Column("closes_at", sa.DateTime(timezone=True)))
    op.add_column("challenges", sa.Column("decided_at", sa.DateTime(timezone=True)))
    # Keyed hashes, like reporter signals: enough to see one network or one contact disputing many
    # numbers, never the address itself.
    op.add_column("challenges", sa.Column("ip_key", sa.String(64)))
    op.add_column("challenges", sa.Column("claimant_key", sa.String(64)))
    op.execute("UPDATE challenges SET closes_at = created_at + interval '7 days' WHERE closes_at IS NULL")
    op.create_index("ix_challenges_ip_time", "challenges", ["ip_key", "created_at"])
    op.create_index(
        "ix_challenges_open_due",
        "challenges",
        ["closes_at"],
        postgresql_where=sa.text("status = 'under_review'"),
    )
    # Reports received up to this time were set aside by an upheld review; the number starts fresh.
    op.add_column("identifiers", sa.Column("cleared_before", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("identifiers", "cleared_before")
    op.drop_index("ix_challenges_open_due", "challenges")
    op.drop_index("ix_challenges_ip_time", "challenges")
    for col in ("claimant_key", "ip_key", "decided_at", "closes_at"):
        op.drop_column("challenges", col)
