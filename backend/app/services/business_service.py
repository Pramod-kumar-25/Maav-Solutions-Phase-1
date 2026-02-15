from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.repositories.business_repository import BusinessRepository
from app.repositories.auth_repository import AuthRepository
from app.models.business import BusinessProfile
from app.schemas.business import BusinessProfileCreate, BusinessProfileUpdate

class BusinessProfileService:
    def __init__(self, business_repo: BusinessRepository, auth_repo: AuthRepository):
        self.business_repo = business_repo
        self.auth_repo = auth_repo

    async def get_profile(self, session: AsyncSession, user_id: UUID) -> BusinessProfile | None:
        """
        Retrieve the Business Profile for a user.
        """
        return await self.business_repo.get_by_user_id(session, user_id)

    async def create_profile(self, session: AsyncSession, user_id: UUID, profile_data: BusinessProfileCreate) -> BusinessProfile:
        """
        Create a new Business Profile.
        
        Orchestration:
        1. Check Existing (1:1 Rule).
        2. Fetch User to validate PAN.
        3. Enforce Business Rules:
           - PAN Type Check: Individual ('P') cannot act as Business Entity directly.
             (Enforces PAN Must NOT be 'P').
           - Constitution Check: Match PAN 4th Char.
        4. Persist in Transaction.
        """
        # 1. Enforce 1:1 Relationship (Read-only check)
        existing_profile = await self.business_repo.get_by_user_id(session, user_id)
        if existing_profile:
            raise ValueError(f"Business profile already exists for user {user_id}")

        # 2. Fetch User for PAN Validation
        user = await self.auth_repo.get_user_by_id(session, user_id)
        if not user:
             raise ValueError("User not found")
        
        pan_char_4 = user.pan[3].upper() # 4th character of PAN (0-indexed)

        # 3. Enforce Business Rules
        
        # Rule A: PAN Type must NOT be 'P' (Individual)
        if pan_char_4 == 'P':
            raise ValueError("Individual PAN (Type 'P') cannot create a Business Profile. Use Taxpayer Profile instead.")

        # Rule B: Constitution Type Match
        # Mapping specific to Indian Income Tax PAN structure
        constitution_map = {
            'C': ['COMPANY', 'PVT_LTD', 'PUBLIC_LTD'],
            'F': ['FIRM', 'LLP', 'PARTNERSHIP'],
            'H': ['HUF'],
            'A': ['AOP', 'BOI'],
            'T': ['TRUST'],
            'L': ['LOCAL_AUTHORITY'],
            'J': ['ARTIFICIAL_JURIDICAL_PERSON'],
            'G': ['GOVERNMENT']
        }

        # Normalize input
        input_const = profile_data.constitution_type.upper()
        
        # Strict Validation: Dictionary key check
        if pan_char_4 not in constitution_map:
             raise ValueError(f"Unknown or unsupported PAN Type '{pan_char_4}' for Business Profile.")
        
        valid_types = constitution_map[pan_char_4]
        
        # Strict Validation: Value check
        if input_const not in valid_types:
             raise ValueError(f"Constitution '{input_const}' does not match PAN Type '{pan_char_4}'. Expected one of: {valid_types}")

        # 4. Transactional Persistence
        async with session.begin():
            new_profile = BusinessProfile(
                user_id=user_id,
                constitution_type=profile_data.constitution_type,
                business_name=profile_data.business_name,
                date_of_incorporation=profile_data.date_of_incorporation,
                # Explicit assignment of booleans
                gst_registered=profile_data.gst_registered,
                gstin=profile_data.gstin,
                tan_available=profile_data.tan_available,
                msme_registered=profile_data.msme_registered,
                iec_available=profile_data.iec_available,
                turnover_bracket=profile_data.turnover_bracket,
                books_maintained=profile_data.books_maintained,
                accounting_method=profile_data.accounting_method,
                registered_state=profile_data.registered_state
            )
            
            saved_profile = await self.business_repo.create_profile(session, new_profile)
            return saved_profile

    async def update_profile(self, session: AsyncSession, user_id: UUID, profile_data: BusinessProfileUpdate) -> BusinessProfile:
         # Placeholder for update logic
         pass
