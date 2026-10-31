"""A fingerprint of the scam message itself, kept apart from the note's.

When a person reports from a pasted message, the message is turned into a MinHash fingerprint
and dropped, like a note. It is stored separately because many real victims paste the same
message: the trust engine reads near-identical notes as one voice, and a mass-sent SMS must not
make its own victims look like a copy-paste brigade. This column is used only for wording search.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("msg_sig", pg.ARRAY(sa.BigInteger), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "msg_sig")
