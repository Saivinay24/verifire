"""Two more privacy-safe note flags: names a scam in general words, reads like a shop review.

Like note_lex, these are single booleans worked out at submit time; the note text is still dropped.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("note_scam", sa.Boolean, nullable=False, server_default=sa.false()))
    op.add_column("reports", sa.Column("note_review", sa.Boolean, nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("reports", "note_review")
    op.drop_column("reports", "note_scam")
