"""create_filing_cases_table

Revision ID: bf729ede8c50
Revises: 386a56dbabbb
Create Date: 2026-02-15 19:30:11.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bf729ede8c50'
down_revision: Union[str, Sequence[str], None] = '386a56dbabbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('filing_cases',
        sa.Column('id', sa.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('financial_year', sa.String(length=9), nullable=False),
        sa.Column('itr_determination_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('current_state', sa.String(length=30), nullable=False),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['itr_determination_id'], ['itr_determinations.id']),
        sa.PrimaryKeyConstraint('id'),
        
        sa.CheckConstraint(
            "current_state IN ('DRAFT', 'READY_FOR_REVIEW', 'LOCKED', 'SUBMITTED')",
            name='check_filing_state_valid'
        ),
        sa.UniqueConstraint('user_id', 'financial_year', name='uq_filing_user_year'),
        sa.UniqueConstraint('itr_determination_id', name='uq_filing_itr_determination')
    )
    
    # Indexes for FKs are good practice
    op.create_index(op.f('ix_filing_cases_user_id'), 'filing_cases', ['user_id'], unique=False)
    op.create_index(op.f('ix_filing_cases_itr_determination_id'), 'filing_cases', ['itr_determination_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_filing_cases_itr_determination_id'), table_name='filing_cases')
    op.drop_index(op.f('ix_filing_cases_user_id'), table_name='filing_cases')
    op.drop_table('filing_cases')
