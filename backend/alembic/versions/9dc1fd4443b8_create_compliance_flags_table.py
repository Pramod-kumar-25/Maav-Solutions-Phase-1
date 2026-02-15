"""create_compliance_flags_table

Revision ID: 9dc1fd4443b8
Revises: 24bb6ee68183
Create Date: 2026-02-15 13:35:01.694012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9dc1fd4443b8'
down_revision: Union[str, Sequence[str], None] = '24bb6ee68183'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop existing table (USER CONFIRMED 0 ROWS, SAFE TO DROP)
    # Using IF EXISTS for safety, though user said table exists.
    # But Alembic op.drop_table doesn't support IF EXISTS easily without raw SQL or checking inspector.
    # Given context, we assume it exists.
    op.drop_table('compliance_flags')

    # 2. Recreate with Strict Schema
    op.create_table(
        'compliance_flags',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('financial_year', sa.String(length=9), nullable=False),
        sa.Column('flag_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint("severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name='check_severity_level')
    )
    
    # Add Index for user lookup
    op.create_index(op.f('ix_compliance_flags_user_id'), 'compliance_flags', ['user_id'], unique=False)


def downgrade() -> None:
    # 1. Drop the new table
    op.drop_index(op.f('ix_compliance_flags_user_id'), table_name='compliance_flags')
    op.drop_table('compliance_flags')

    # 2. Restore Legacy Schema (Best Effort based on previous inspection)
    op.create_table(
        'compliance_flags',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('taxpayer_id', sa.UUID(), nullable=False),
        sa.Column('rule_code', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'OPEN'"), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['taxpayer_id'], ['taxpayer_profiles.id'], ondelete='CASCADE')
    )
    op.create_index('idx_compliance_taxpayer', 'compliance_flags', ['taxpayer_id'], unique=False)
