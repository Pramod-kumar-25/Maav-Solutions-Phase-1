"""refactor_financials_to_user_id

Revision ID: 733415172ba8
Revises: 9a54bfb1c477
Create Date: 2026-02-15 12:11:04.583002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '733415172ba8'
down_revision: Union[str, Sequence[str], None] = '9a54bfb1c477'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Income Records
    # Add nullable user_id
    op.add_column('income_records', sa.Column('user_id', UUID(as_uuid=True), nullable=True))
    
    # Backfill user_id from taxpayer_profiles
    op.execute("""
        UPDATE income_records
        SET user_id = taxpayer_profiles.user_id
        FROM taxpayer_profiles
        WHERE income_records.taxpayer_id = taxpayer_profiles.id
    """)

    # Enforce NOT NULL
    op.alter_column('income_records', 'user_id', nullable=False)
    
    # Create Foreign Key
    op.create_foreign_key(None, 'income_records', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('idx_income_user'), 'income_records', ['user_id'], unique=False)
    
    # Drop old column and FK
    op.drop_constraint('income_records_taxpayer_id_fkey', 'income_records', type_='foreignkey')
    op.drop_index('idx_income_taxpayer', table_name='income_records')
    op.drop_column('income_records', 'taxpayer_id')

    # 2. Expense Records
    # Add nullable user_id
    op.add_column('expense_records', sa.Column('user_id', UUID(as_uuid=True), nullable=True))
    
    # Backfill user_id from business_entities
    op.execute("""
        UPDATE expense_records
        SET user_id = business_entities.owner_user_id
        FROM business_entities
        WHERE expense_records.business_id = business_entities.id
    """)

    # Enforce NOT NULL
    op.alter_column('expense_records', 'user_id', nullable=False)
    
    # Create Foreign Key
    op.create_foreign_key(None, 'expense_records', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('idx_expense_user'), 'expense_records', ['user_id'], unique=False)
    
    # Drop old column and FK
    op.drop_constraint('expense_records_business_id_fkey', 'expense_records', type_='foreignkey')
    op.drop_index('idx_expense_business', table_name='expense_records')
    op.drop_column('expense_records', 'business_id')


def downgrade() -> None:
    # Reverse operations for Income Records
    op.add_column('income_records', sa.Column('taxpayer_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('income_records_taxpayer_id_fkey', 'income_records', 'taxpayer_profiles', ['taxpayer_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_income_taxpayer', 'income_records', ['taxpayer_id'], unique=False)
    
    # Backfill taxpayer_id (Best effort: assumes 1:1 user-taxpayer)
    op.execute("""
        UPDATE income_records
        SET taxpayer_id = taxpayer_profiles.id
        FROM taxpayer_profiles
        WHERE income_records.user_id = taxpayer_profiles.user_id
    """)
    
    op.alter_column('income_records', 'taxpayer_id', nullable=False)
    op.drop_constraint(None, 'income_records', type_='foreignkey') # Drop user_id FK
    op.drop_index(op.f('idx_income_user'), table_name='income_records')
    op.drop_column('income_records', 'user_id')

    # Reverse operations for Expense Records
    op.add_column('expense_records', sa.Column('business_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('expense_records_business_id_fkey', 'expense_records', 'business_entities', ['business_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_expense_business', 'expense_records', ['business_id'], unique=False)

    # Backfill business_id (Best effort: assumes 1:1 user-business)
    op.execute("""
        UPDATE expense_records
        SET business_id = business_entities.id
        FROM business_entities
        WHERE expense_records.user_id = business_entities.owner_user_id
    """)

    op.alter_column('expense_records', 'business_id', nullable=False)
    op.drop_constraint(None, 'expense_records', type_='foreignkey') # Drop user_id FK
    op.drop_index(op.f('idx_expense_user'), table_name='expense_records')
    op.drop_column('expense_records', 'user_id')
