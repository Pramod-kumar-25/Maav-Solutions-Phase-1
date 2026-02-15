from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from decimal import Decimal
from app.models.financials import FinancialEntry

class BaseComplianceRule(ABC):
    """
    Abstract Base Class for Compliance Rules.
    Rules must be pure evaluators:
    - Input: List of FinancialEntry objects.
    - Output: Violation Dict or None.
    - No DB access allowed.
    """
    rule_code: str
    severity: str

    @abstractmethod
    def evaluate(self, entries: List[FinancialEntry]) -> Optional[Dict[str, Any]]:
        """
        Evaluate the rule against the provided entries.
        Returns None if compliant, or a dict with violation details if not.
        """
        pass

class HighTotalExpenseRule(BaseComplianceRule):
    """
    Flag if total expenses exceed a specific threshold (e.g., 50 Lakhs).
    """
    rule_code = "C001"
    severity = "HIGH"
    THRESHOLD = Decimal("5000000.00")  # 50 Lakhs

    def evaluate(self, entries: List[FinancialEntry]) -> Optional[Dict[str, Any]]:
        total_expenses = sum(
            entry.amount for entry in entries 
            if entry.entry_type == "EXPENSE"
        )

        if total_expenses > self.THRESHOLD:
            return {
                "flag_code": self.rule_code,
                "severity": self.severity,
                "description": f"Total expenses ({total_expenses}) exceed high value threshold ({self.THRESHOLD})."
            }
        return None

class ExpenseWithoutIncomeRule(BaseComplianceRule):
    """
    Flag if expenses exist but no income is recorded for the financial year.
    """
    rule_code = "C002"
    severity = "CRITICAL"

    def evaluate(self, entries: List[FinancialEntry]) -> Optional[Dict[str, Any]]:
        has_expenses = any(entry.entry_type == "EXPENSE" for entry in entries)
        total_income = sum(
            entry.amount for entry in entries 
            if entry.entry_type == "INCOME"
        )

        if has_expenses and total_income == 0:
            return {
                "flag_code": self.rule_code,
                "severity": self.severity,
                "description": "Expenses recorded without any corresponding income for the financial year."
            }
        return None
