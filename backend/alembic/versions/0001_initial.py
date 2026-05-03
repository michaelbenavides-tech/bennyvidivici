"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-03
"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.db import Base
    from app.models import Organization

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.db import Base

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
