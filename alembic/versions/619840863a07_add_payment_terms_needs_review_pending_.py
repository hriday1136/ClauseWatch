"""add payment_terms, needs_review, pending_review

Revision ID: 619840863a07
Revises: 95e51469c4a6
Create Date: 2026-08-03 20:05:08.431900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '619840863a07'
down_revision: Union[str, Sequence[str], None] = '95e51469c4a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE clausetype ADD VALUE 'payment_terms'")
        op.execute("ALTER TYPE contractstatus ADD VALUE 'pending_review'")

    op.add_column('clauses', sa.Column('needs_review', sa.Boolean(), nullable=False, server_default='false'))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('clauses', 'needs_review')
    # Postgres does not support removing values from an existing ENUM type.
    # Downgrading this migration will not remove 'payment_terms' or 'pending_review'
    # from their enum types — accepted limitation.
    # ### end Alembic commands ###
