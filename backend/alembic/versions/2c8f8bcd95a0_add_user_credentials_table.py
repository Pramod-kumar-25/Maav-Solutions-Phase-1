"""add_user_credentials_table

Revision ID: 2c8f8bcd95a0
Revises: 9ddd885ea444
Create Date: 2026-02-14 14:36:28.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '2c8f8bcd95a0'
down_revision: Union[str, None] = '9ddd885ea444'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create table user_credentials
    op.create_table(
        'user_credentials',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('auth_provider', sa.String(length=30), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('failed_attempts', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'auth_provider', name='unique_user_provider'),
        sa.CheckConstraint("auth_provider IN ('PASSWORD')", name='check_auth_provider')
    )

    # 2. Add indexes
    op.create_index('idx_credentials_user', 'user_credentials', ['user_id'])
    op.create_index('idx_credentials_provider', 'user_credentials', ['auth_provider'])


def downgrade() -> None:
    # Drop table user_credentials
    op.drop_table('user_credentials')
