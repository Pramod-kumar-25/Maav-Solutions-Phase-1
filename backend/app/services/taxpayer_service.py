from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.repositories.taxpayer_repository import TaxpayerRepository
from app.models.taxpayer import TaxpayerProfile
from app.schemas.taxpayer import TaxpayerProfileCreate, TaxpayerProfileUpdate, TaxpayerProfileResponse
from app.engines.classification import calculate_residential_status, ResidentialStatus

class TaxpayerProfileService:
    def __init__(self, taxpayer_repo: TaxpayerRepository):
        self.taxpayer_repo = taxpayer_repo

    async def get_profile(self, session: AsyncSession, user_id: UUID) -> TaxpayerProfile | None:
        """
        Retrieve the Taxpayer Profile for a user.
        """
        return await self.taxpayer_repo.get_by_user_id(session, user_id)

    async def create_profile(self, session: AsyncSession, user_id: UUID, profile_data: TaxpayerProfileCreate) -> TaxpayerProfile:
        """
        Create a new Taxpayer Profile.
        
        Orchestration:
        1. Check Existing (1:1 Rule).
        2. Calculate Residential Status (Engine).
        3. Enforce Business Rules (No NRI in Phase 1).
        4. Persist in Transaction.
        """
        # 1. Enforce 1:1 Relationship (Read-only check)
        existing_profile = await self.taxpayer_repo.get_by_user_id(session, user_id)
        if existing_profile:
            raise ValueError(f"Taxpayer profile already exists for user {user_id}")

        # 2. Engine Calculation (Pure Logic)
        # Phase 1: We use the Basic Residency Tests (182 days / 60+365 days).
        # - 'has_foreign_income' is stored for record but does NOT affect classification 
        #   in Phase 1 (120-day rule for citizens > 15L income is deferred to Phase 2).
        # - Advanced parameters (citizenship, total_income, taxed_elsewhere) are not 
        #   captured in Phase 1 inputs, so we pass neutral/default values.
        res_status = calculate_residential_status(
            days_in_india_current_fy=profile_data.days_in_india_current_fy,
            days_in_india_last_4_years=profile_data.days_in_india_last_4_years,
            # Forward compatibility args (Explicitly passed as defaults for Phase 1)
            is_indian_citizen=False, 
            total_income_excluding_foreign_income=None,
            taxed_elsewhere=None
        )

        # 3. Enforce Business Rules (Phase 1 Limits)
        if res_status == ResidentialStatus.NRI:
            raise ValueError("Phase 1 currently supports RESIDENT and RNOR status only. NRI support is pending.")

        # 4. Transactional Persistence
        # We rely on the caller or framework to handle exceptions. 
        # async with session.begin() ensures atomicity.
        async with session.begin():
            new_profile = TaxpayerProfile(
                user_id=user_id,
                residential_status=res_status.value,
                days_in_india_current_fy=profile_data.days_in_india_current_fy,
                days_in_india_last_4_years=profile_data.days_in_india_last_4_years,
                has_foreign_income=profile_data.has_foreign_income,
                default_tax_regime=profile_data.default_tax_regime,
                aadhaar_link_status=profile_data.aadhaar_link_status
            )
            
            saved_profile = await self.taxpayer_repo.create_profile(session, new_profile)
            return saved_profile

    async def update_profile(self, session: AsyncSession, user_id: UUID, profile_data: TaxpayerProfileUpdate) -> TaxpayerProfile:
         # Placeholder for update logic (re-calculation needed if days change)
         pass
