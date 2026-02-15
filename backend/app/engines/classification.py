"""
Residential Classification Engine
Phase 1: Deterministic Logic for Individual Taxpayers.
Based on Income Tax Act, 1961 - Section 6.

This module implements the Basic Residency Tests for Phase 1.
Advanced rules like Deemed Residency (6(1A)) and the 120-day rule (6(1)(b)) 
are defined in the signature for forward compatibility but deferred to Phase 2.
"""
from enum import Enum
from typing import Optional

class ResidentialStatus(str, Enum):
    """
    Residential Status Enum.
    Matches database constraints and application logic.
    """
    RESIDENT = "RESIDENT"
    RNOR = "RNOR"
    NRI = "NRI"

def calculate_residential_status(
    days_in_india_current_fy: int,
    days_in_india_last_4_years: Optional[int] = 0,
    # Forward Compatibility Parameters (Not used in Phase 1 logic)
    is_indian_citizen: bool = False,
    total_income_excluding_foreign_income: Optional[float] = None,
    taxed_elsewhere: Optional[bool] = None
) -> ResidentialStatus:
    """
    Determines the Residential Status of an Individual based on physical presence.
    
    Args:
        days_in_india_current_fy (int): Number of days in India during the current Financial Year.
        days_in_india_last_4_years (int): Total days in India during the preceding 4 Financial Years.
        is_indian_citizen (bool): Status of Indian Citizenship (For 6(1)(b) and 6(1A)).
        total_income_excluding_foreign_income (float): Total Indian Income (For >15L checks).
        taxed_elsewhere (bool): If the individual is liable to tax in any other country (For 6(1A)).

    Returns:
        ResidentialStatus: RESIDENT, RNOR, or NRI.

    Logic Implemented (Phase 1):
    1. **182-Day Rule** (Section 6(1)(a)): 
       - If days_in_india_current_fy >= 182 -> RESIDENT.
       
    2. **60 + 365 Rule** (Section 6(1)(c)):
       - If days_in_india_current_fy >= 60 AND days_last_4_years >= 365 -> RESIDENT.

    Logic Deferred (TODO Phase 2):
    1. **120-Day Rule** (Section 6(1)(b) - Finance Act 2020):
       - For Citizens/PIOs with Indian Income > 15L.
       - Replaces the 60-day threshold.
       - If 120 <= days < 182 AND days_prev_4 >= 365 -> RNOR.
       
    2. **Deemed Resident** (Section 6(1A)):
       - For Citizens with Indian Income > 15L not taxed elsewhere.
       - Returns RNOR logic.
       
    3. **RNOR Determination** (Section 6(6)):
       - Determines if a RESIDENT is ROR or RNOR.
       - Currently, we default to RESIDENT if the basic tests are met.
    """
    
    # 0. Validation
    if days_in_india_current_fy < 0:
        raise ValueError("Days in India (Current FY) cannot be negative.")
    
    if days_in_india_last_4_years is not None and days_in_india_last_4_years < 0:
        raise ValueError("Days in India (Last 4 Years) cannot be negative.")

    if total_income_excluding_foreign_income is not None and total_income_excluding_foreign_income < 0:
        raise ValueError("Total Income cannot be negative.")

    # Treat None as 0 for days
    days_prev_4 = days_in_india_last_4_years or 0

    # 1. Basic Residency Tests (Section 6(1))
    
    # Rule A: 182 Days Test (Section 6(1)(a))
    if days_in_india_current_fy >= 182:
        # TODO Phase 2: Insert RNOR (6(6)) check here.
        # IF (9/10 years NRI) or (729 days/7 years presence) -> RNOR
        # ELSE -> ROR (Resident)
        return ResidentialStatus.RESIDENT
    
    # TODO Phase 2: Insert 120-Day Rule (Section 6(1)(b)) here.
    # Logic: For Citizens/PIOs with Total Income > 15L:
    # IF 120 <= days_in_india_current_fy < 182 AND days_prev_4 >= 365 -> RETURN RNOR.
    # This rule effectively overrides the '60' days requirement below for this specific cohort.
    
    # Rule B: 60 Days + 365 Days Test (Section 6(1)(c))
    # Note: In Phase 2, this must handle the exception for Citizens visiting India (where 60 becomes 182, unless caught by 120-day rule).
    # For Phase 1, we implement the standard rule without exceptions.
    if days_in_india_current_fy >= 60 and days_prev_4 >= 365:
        return ResidentialStatus.RESIDENT
        
    # TODO Phase 2: Insert Deemed Resident Logic (Section 6(1A)) here.
    # Logic: IF is_indian_citizen AND Total Income > 15L AND NOT taxed_elsewhere:
    # RETURN RNOR
    # This check happens only if the individual fails the physical presence tests above.
    
    # 2. Fallback
    return ResidentialStatus.NRI
