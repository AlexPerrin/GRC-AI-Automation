"""
Human-submitted form schemas for Stage 1 (Use Case) and Stage 4 (Financial Risk).

These schemas serve dual purpose:
  - Validate form submissions stored in Review.form_input
  - Drive automatic frontend form generation (Day 6)
"""
from typing import List, Literal, Optional

from pydantic import BaseModel


class UseCaseFormInput(BaseModel):
    """Stage 1 — Product/Use Case Evaluation (human reviewer)."""
    use_case_description: str
    business_justification: str
    data_types_involved: List[str]
    estimated_users: int
    alternatives_considered: str
    reviewer_name: str
    recommendation: Literal["PROCEED", "DO_NOT_PROCEED"]
    notes: Optional[str] = None


class FinancialRiskFormInput(BaseModel):
    """Stage 4 — Financial Risk Evaluation (human reviewer)."""
    vendor_annual_revenue: Optional[str] = None
    years_in_operation: Optional[int] = None
    financial_documents_reviewed: List[str]
    concentration_risk_flag: bool
    financial_stability_assessment: Literal["STABLE", "CONCERN", "HIGH_RISK"]
    contract_value: Optional[str] = None
    reviewer_name: str
    recommendation: Literal["ACCEPTABLE", "ACCEPTABLE_WITH_CONDITIONS", "UNACCEPTABLE"]
    conditions: Optional[List[str]] = None
    notes: Optional[str] = None
