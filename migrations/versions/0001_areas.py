"""Areas table seeded with the 25 Appendix B areas.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

from app.domain.areas import AREAS

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    areas = op.create_table(
        "areas",
        sa.Column("pincode", sa.String(6), primary_key=True),
        sa.Column("locality", sa.Text, nullable=False),
        sa.Column("city", sa.Text, nullable=False),
        sa.Column("lat", sa.Float, nullable=False),
        sa.Column("lng", sa.Float, nullable=False),
    )
    op.bulk_insert(areas, [a._asdict() for a in AREAS])


def downgrade() -> None:
    op.drop_table("areas")
