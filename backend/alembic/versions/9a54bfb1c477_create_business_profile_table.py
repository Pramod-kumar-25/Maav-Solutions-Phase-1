"""create_business_profile_table

Revision ID: 9a54bfb1c477
Revises: d0ae6ede2c2f
Create Date: 2026-02-15 10:57:06.167103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a54bfb1c477'
down_revision: Union[str, Sequence[str], None] = 'd0ae6ede2c2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'business_profiles',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('constitution_type', sa.String(), nullable=False),
        sa.Column('business_name', sa.Text(), nullable=False),
        sa.Column('date_of_incorporation', sa.Date(), nullable=False),
        sa.Column('gst_registered', sa.Boolean(), nullable=False),
        sa.Column('gstin', sa.String(), nullable=True),
        sa.Column('tan_available', sa.Boolean(), nullable=False),
        sa.Column('msme_registered', sa.Boolean(), nullable=False),
        sa.Column('iec_available', sa.Boolean(), nullable=False),
        sa.Column('turnover_bracket', sa.String(), nullable=False),
        sa.Column('books_maintained', sa.Boolean(), nullable=False),
        sa.Column('accounting_method', sa.String(), nullable=False),
        sa.Column('registered_state', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('business_profiles')
