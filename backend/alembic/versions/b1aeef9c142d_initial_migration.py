"""initial_migration

Revision ID: b1aeef9c142d
Revises:
Create Date: 2026-06-28 22:21:24.482241
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1aeef9c142d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Initial schema: create all tables from SQLAlchemy models."""
    from app.core.database import Base
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Drop all tables."""
    from app.core.database import Base
    Base.metadata.drop_all(bind=op.get_bind())
