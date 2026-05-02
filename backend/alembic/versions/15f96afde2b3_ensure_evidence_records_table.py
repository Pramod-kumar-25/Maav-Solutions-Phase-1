"""\ensure_evidence_records_table\

Revision ID: 15f96afde2b3
Revises: 4d45c786fb18
Create Date: 2026-05-02 08:40:19.518817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15f96afde2b3'
down_revision: Union[str, Sequence[str], None] = '4d45c786fb18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure evidence_records table exists
    op.create_table(
        'evidence_records',
        sa.Column('id', sa.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('related_action', sa.Text(), nullable=True),
        sa.Column('hash', sa.Text(), nullable=False),
        sa.Column('storage_location', sa.Text(), nullable=False),
        sa.Column('retention_expiry', sa.Date(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('evidence_records')
