from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class SalaryAdvanceRequest(BaseModel):
    requested_advance_amount: float = Field(
        gt=0, description="Requested advance amount must be greater than 0"
    )


class AdvanceCalculationRequest(BaseModel):
    gross_salary: float = Field(gt=0, description="Gross salary must be greater than 0")
    pay_frequency: str = Field(..., description="Pay frequency")
    employee_id: str = Field(..., description="Employee ID")
    salary_advance: SalaryAdvanceRequest


class LoanCalculationRequest(BaseModel):
    employee_id: str = Field(..., description="Employee ID")
    loan_amount: float = Field(gt=0, description="Loan amount must be greater than 0")
    annual_interest_rate: float = Field(
        ge=0, le=1.0, description="Interest rate must be between 0 and 1.0"
    )
    loan_term_months: int = Field(
        gt=0, description="Loan term must be greater than 0 months"
    )


class EligibilityDetails(BaseModel):
    is_eligible: bool
    failed_criteria: List[str]
    max_eligible_advance: Optional[float]
    salary_check: bool
    pay_frequency_check: bool
    amount_check: bool
    advance_limit_check: bool


class AdvanceCalculationResponse(BaseModel):
    error: bool
    error_message: str
    advance_eligible: bool
    advance_message: str
    approved_advance_amount: Optional[float]
    eligibility_details: Optional[EligibilityDetails]


class LoanCalculationResponse(BaseModel):
    error: bool
    error_message: str
    loan_requested: bool
    loan_total_repayable_amount: Optional[float]
    loan_amortization_schedule: Optional[List[dict]]


class LoanRecord(BaseModel):
    employee_id: str
    loan_type: str
    amount: float
    interest_rate: float
    loan_term_months: int
    disbursement_date: datetime
    expected_repayment_date: datetime
    status: str
    created_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
