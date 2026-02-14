"""initial_schema

Revision ID: 9ddd885ea444
Revises: 
Create Date: 2026-02-13 16:53:28.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB

# revision identifiers, used by Alembic.
revision: str = '9ddd885ea444'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # 2. Users Table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('pan', sa.String(length=10), nullable=False),
        sa.Column('legal_name', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('mobile', sa.String(length=15), nullable=False),
        sa.Column('primary_role', sa.String(length=20), nullable=False),
        sa.Column('account_status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(pan) = 10", name='check_pan_length'),
        sa.CheckConstraint("primary_role IN ('INDIVIDUAL','BUSINESS','CA','ADMIN')", name='check_user_role'),
        sa.UniqueConstraint('pan', name='unique_pan'),
        sa.UniqueConstraint('email', name='unique_email')
    )

    # 3. Auth Sessions
    op.create_table(
        'auth_sessions',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('auth_method', sa.String(length=20), nullable=False),
        sa.Column('device_id', sa.Text(), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('session_start', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('session_expiry', sa.TIMESTAMP(timezone=True), nullable=False)
    )
    op.create_index('idx_auth_user', 'auth_sessions', ['user_id'])

    # 4. Consent Artifacts
    op.create_table(
        'consent_artifacts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('purpose', sa.String(length=50), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('consent_version', sa.String(length=20), nullable=True),
        sa.Column('granted_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expiry_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')", name='check_consent_status')
    )
    op.create_index('idx_consent_user', 'consent_artifacts', ['user_id'])

    # 5. Consent Audit Logs
    op.create_table(
        'consent_audit_logs',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('consent_id', UUID(as_uuid=True), sa.ForeignKey('consent_artifacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('actor_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_consent_audit_consent', 'consent_audit_logs', ['consent_id'])
    op.create_index('idx_consent_audit_actor', 'consent_audit_logs', ['actor_id'])

    # 6. Taxpayer Profiles
    op.create_table(
        'taxpayer_profiles',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pan_type', sa.CHAR(length=1), nullable=False),
        sa.Column('residential_status', sa.String(length=20), nullable=True),
        sa.Column('default_tax_regime', sa.String(length=20), server_default='NEW', nullable=False),
        sa.Column('aadhaar_link_status', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("residential_status IN ('RESIDENT','RNOR','NRI')", name='check_res_status'),
        sa.UniqueConstraint('user_id', name='unique_taxpayer_user')
    )

    # 7. Business Entities
    op.create_table(
        'business_entities',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('owner_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', sa.String(length=30), nullable=False),
        sa.Column('gstin', sa.String(length=15), nullable=True),
        sa.Column('msme_status', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('incorporation_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('gstin', name='unique_gstin')
    )
    op.create_index('idx_business_owner', 'business_entities', ['owner_user_id'])

    # 8. Data Sources
    op.create_table(
        'data_sources',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('source_type', sa.String(length=30), nullable=False),
        sa.Column('reference_number', sa.Text(), nullable=True),
        sa.Column('retrieved_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("source_type IN ('AIS','AA','UPLOAD')", name='check_source_type')
    )

    # 9. Income Records
    op.create_table(
        'income_records',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('taxpayer_id', UUID(as_uuid=True), sa.ForeignKey('taxpayer_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('income_head', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('financial_year', sa.String(length=9), nullable=False),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('data_sources.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount >= 0", name='check_income_amount')
    )
    op.create_index('idx_income_taxpayer', 'income_records', ['taxpayer_id'])
    op.create_index('idx_income_source', 'income_records', ['source_id'])

    # 10. Expense Records
    op.create_table(
        'expense_records',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('business_id', UUID(as_uuid=True), sa.ForeignKey('business_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('payment_mode', sa.String(length=20), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('msme_flag', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount >= 0", name='check_expense_amount')
    )
    op.create_index('idx_expense_business', 'expense_records', ['business_id'])

    # 11. Compliance Flags
    op.create_table(
        'compliance_flags',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('taxpayer_id', UUID(as_uuid=True), sa.ForeignKey('taxpayer_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_code', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('triggered_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='OPEN', nullable=False),
        sa.CheckConstraint("severity IN ('HARD','SOFT')", name='check_severity')
    )
    op.create_index('idx_compliance_taxpayer', 'compliance_flags', ['taxpayer_id'])

    # 12. ITR Determinations
    op.create_table(
        'itr_determinations',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('taxpayer_id', UUID(as_uuid=True), sa.ForeignKey('taxpayer_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('financial_year', sa.String(length=9), nullable=False),
        sa.Column('itr_type', sa.String(length=10), nullable=False),
        sa.Column('locked_by', sa.String(length=20), nullable=True),
        sa.Column('lock_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_itr_taxpayer', 'itr_determinations', ['taxpayer_id'])

    # 13. Filing Cases
    op.create_table(
        'filing_cases',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('taxpayer_id', UUID(as_uuid=True), sa.ForeignKey('taxpayer_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('financial_year', sa.String(length=9), nullable=False),
        sa.Column('filing_mode', sa.String(length=20), nullable=False),
        sa.Column('current_state', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("filing_mode IN ('SELF','CA')", name='check_filing_mode')
    )
    op.create_index('idx_filing_taxpayer', 'filing_cases', ['taxpayer_id'])

    # 14. Submission Records
    op.create_table(
        'submission_records',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('filing_id', UUID(as_uuid=True), sa.ForeignKey('filing_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attempt_no', sa.Integer(), nullable=False),
        sa.Column('ack_number', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True)
    )
    op.create_index('idx_submission_filing', 'submission_records', ['filing_id'])

    # 15. User Confirmations
    op.create_table(
        'user_confirmations',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('filing_id', UUID(as_uuid=True), sa.ForeignKey('filing_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('confirmation_type', sa.String(length=50), nullable=False),
        sa.Column('confirmed_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('confirmed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_user_confirm_filing', 'user_confirmations', ['filing_id'])
    op.create_index('idx_user_confirm_user', 'user_confirmations', ['confirmed_by'])

    # 16. CA Assignments
    op.create_table(
        'ca_assignments',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('filing_id', UUID(as_uuid=True), sa.ForeignKey('filing_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ca_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('consent_id', UUID(as_uuid=True), sa.ForeignKey('consent_artifacts.id'), nullable=False),
        sa.Column('assigned_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True)
    )
    op.create_index('idx_ca_assign_filing', 'ca_assignments', ['filing_id'])
    op.create_index('idx_ca_assign_user', 'ca_assignments', ['ca_user_id'])
    op.create_index('idx_ca_assign_consent', 'ca_assignments', ['consent_id'])

    # 17. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('actor_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_role', sa.String(length=20), nullable=True),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('before_value', JSONB(), nullable=True),
        sa.Column('after_value', JSONB(), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('device_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_audit_actor', 'audit_logs', ['actor_id'])

    # 18. Evidence Records
    op.create_table(
        'evidence_records',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('related_action', sa.Text(), nullable=True),
        sa.Column('hash', sa.Text(), nullable=False),
        sa.Column('storage_location', sa.Text(), nullable=False),
        sa.Column('retention_expiry', sa.Date(), nullable=True)
    )


def downgrade() -> None:
    # Drop in reverse order of dependencies
    op.drop_table('evidence_records')
    op.drop_table('audit_logs')
    op.drop_table('ca_assignments')
    op.drop_table('user_confirmations')
    op.drop_table('submission_records')
    op.drop_table('filing_cases')
    op.drop_table('itr_determinations')
    op.drop_table('compliance_flags')
    op.drop_table('expense_records')
    op.drop_table('income_records')
    op.drop_table('data_sources')
    op.drop_table('business_entities')
    op.drop_table('taxpayer_profiles')
    op.drop_table('consent_audit_logs')
    op.drop_table('consent_artifacts')
    op.drop_table('auth_sessions')
    op.drop_table('users')
