"""create_itr_determinations_table

Revision ID: 386a56dbabbb
Revises: 9dc1fd4443b8
Create Date: 2026-02-15 16:32:17.243714

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '386a56dbabbb'
down_revision: Union[str, Sequence[str], None] = '9dc1fd4443b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure clean slate: Drop old table if exists (Safe Reset)
    op.execute("DROP TABLE IF EXISTS itr_determinations CASCADE")

    op.create_table('itr_determinations',
        sa.Column('id', sa.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('financial_year', sa.String(length=9), nullable=False),
        sa.Column('itr_type', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('is_locked', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('determined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("itr_type IN ('ITR-1', 'ITR-2', 'ITR-3')", name='check_itr_type_valid'),
        sa.UniqueConstraint('user_id', 'financial_year', name='uq_itr_user_financial_year')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('itr_determinations')
