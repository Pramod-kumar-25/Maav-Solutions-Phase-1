"""unify_financial_ledger

Revision ID: 24bb6ee68183
Revises: 733415172ba8
Create Date: 2026-02-15 12:25:40.373152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '24bb6ee68183'
down_revision: Union[str, Sequence[str], None] = '733415172ba8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create financial_entries table
    op.create_table('financial_entries',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('entry_type', sa.String(length=10), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('financial_year', sa.String(length=9), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("entry_type IN ('INCOME', 'EXPENSE')", name='check_entry_type'),
        sa.CheckConstraint('amount >= 0', name='check_amount_positive'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_entries_user_id'), 'financial_entries', ['user_id'], unique=False)

    # 2. Backfill from income_records
    op.execute("""
        INSERT INTO financial_entries (
            id, user_id, entry_type, category, amount, 
            financial_year, entry_date, description, created_at
        )
        SELECT
            uuid_generate_v4(),
            user_id,
            'INCOME',
            income_head,
            amount,
            financial_year,
            created_at::date,
            'Source ID: ' || COALESCE(source_id::text, 'None'),
            created_at
        FROM income_records
    """)

    # 3. Backfill from expense_records
    # Note: Deriving financial_year safely from invoice_date or created_at
    # Logic: If month >= 4 (April), then FY is current_year-next_year_suffix (e.g., 2024-25)
    #        Else, previous_year-current_year_suffix (e.g., 2023-24)
    op.execute("""
        INSERT INTO financial_entries (
            id, user_id, entry_type, category, amount, 
            financial_year, entry_date, description, created_at
        )
        SELECT
            uuid_generate_v4(),
            user_id,
            'EXPENSE',
            COALESCE(category, 'Uncategorized'),
            amount,
            CASE 
                WHEN EXTRACT(MONTH FROM COALESCE(invoice_date, created_at::date)) >= 4 
                THEN TO_CHAR(COALESCE(invoice_date, created_at::date), 'YYYY') || '-' || SUBSTRING(TO_CHAR(COALESCE(invoice_date, created_at::date) + INTERVAL '1 year', 'YYYY') FROM 3 FOR 2)
                ELSE TO_CHAR(COALESCE(invoice_date, created_at::date) - INTERVAL '1 year', 'YYYY') || '-' || SUBSTRING(TO_CHAR(COALESCE(invoice_date, created_at::date), 'YYYY') FROM 3 FOR 2)
            END,
            COALESCE(invoice_date, created_at::date),
            'Payment Mode: ' || COALESCE(payment_mode, 'Unknown') || '; MSME: ' || msme_flag::text,
            created_at
        FROM expense_records
    """)

    # 4. Drop old tables (BUT KEEP data_sources)
    op.drop_index(op.f('idx_expense_user'), table_name='expense_records')
    op.drop_table('expense_records')
    
    op.drop_index(op.f('idx_income_source'), table_name='income_records')
    op.drop_index(op.f('idx_income_user'), table_name='income_records')
    op.drop_table('income_records')


def downgrade() -> None:
    # 1. Recreate Income Records
    op.create_table('income_records',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('income_head', sa.VARCHAR(length=50), nullable=False),
        sa.Column('amount', sa.NUMERIC(precision=15, scale=2), nullable=False),
        sa.Column('financial_year', sa.VARCHAR(length=9), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.CheckConstraint('amount >= 0::numeric', name='check_income_amount'),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], name='income_records_source_id_fkey'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='income_records_user_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='income_records_pkey')
    )
    op.create_index('idx_income_user', 'income_records', ['user_id'], unique=False)
    op.create_index('idx_income_source', 'income_records', ['source_id'], unique=False)

    # 2. Recreate Expense Records
    op.create_table('expense_records',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('category', sa.VARCHAR(length=50), nullable=True),
        sa.Column('amount', sa.NUMERIC(precision=15, scale=2), nullable=False),
        sa.Column('payment_mode', sa.VARCHAR(length=20), nullable=True),
        sa.Column('invoice_date', sa.DATE(), nullable=True),
        sa.Column('msme_flag', sa.BOOLEAN(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.CheckConstraint('amount >= 0::numeric', name='check_expense_amount'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='expense_records_user_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='expense_records_pkey')
    )
    op.create_index('idx_expense_user', 'expense_records', ['user_id'], unique=False)

    # 3. Restore Data (Best Effort Logic)
    # Income
    op.execute("""
        INSERT INTO income_records (
            id, user_id, income_head, amount, financial_year, created_at
        )
        SELECT
            uuid_generate_v4(),
            user_id,
            category,
            amount,
            financial_year,
            created_at
        FROM financial_entries
        WHERE entry_type = 'INCOME'
    """)

    # Expense
    op.execute("""
        INSERT INTO expense_records (
            id, user_id, category, amount, invoice_date, created_at
        )
        SELECT
            uuid_generate_v4(),
            user_id,
            category,
            amount,
            entry_date,
            created_at
        FROM financial_entries
        WHERE entry_type = 'EXPENSE'
    """)

    # 4. Drop Financial Entries
    op.drop_index(op.f('ix_financial_entries_user_id'), table_name='financial_entries')
    op.drop_table('financial_entries')
