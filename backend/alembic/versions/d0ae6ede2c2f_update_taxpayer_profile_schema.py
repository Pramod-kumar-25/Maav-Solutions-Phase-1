"""update_taxpayer_profile_schema

Revision ID: d0ae6ede2c2f
Revises: 2c8f8bcd95a0
Create Date: 2026-02-14 22:34:05.259912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0ae6ede2c2f'
down_revision: Union[str, Sequence[str], None] = '2c8f8bcd95a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Taxpayer Profile Updates
    op.add_column('taxpayer_profiles', sa.Column('days_in_india_current_fy', sa.Integer(), nullable=True))
    op.add_column('taxpayer_profiles', sa.Column('days_in_india_last_4_years', sa.Integer(), nullable=True))
    
    # 1. Add column with server default to safe backfill existing rows
    op.add_column(
        'taxpayer_profiles',
        sa.Column('has_foreign_income', sa.Boolean(), server_default=sa.text('false'), nullable=False)
    )
    # 2. Drop server default to enforce application-level explicit input for future rows
    op.alter_column('taxpayer_profiles', 'has_foreign_income', server_default=None)
    
    op.drop_column('taxpayer_profiles', 'pan_type')


def downgrade() -> None:
    """Downgrade schema."""
    # Taxpayer Profile RESTORE
    # Restoring pan_type as nullable because data was dropped
    op.add_column('taxpayer_profiles', sa.Column('pan_type', sa.CHAR(length=1), nullable=True))
    
    op.drop_column('taxpayer_profiles', 'has_foreign_income')
    op.drop_column('taxpayer_profiles', 'days_in_india_last_4_years')
    op.drop_column('taxpayer_profiles', 'days_in_india_current_fy')
