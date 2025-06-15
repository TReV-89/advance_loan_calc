import fastapi
import pandas as pd
import datetime
from calculations import (
    calculate_advance_amount,
    calculate_total_repayable_loan_amount,
    generate_amortization_schedule,
    record_loan,
)
import os
from pydantic_models import (
    AdvanceCalculationRequest,
    LoanCalculationRequest,
    EligibilityDetails,
    AdvanceCalculationResponse,
    LoanCalculationResponse,
    LoanRecord,
)
from typing import List

DATA_DIR = "data"
LOANS_CSV_FILE = os.path.join(DATA_DIR, "loans.csv")

os.makedirs(DATA_DIR, exist_ok=True)


def initialize_empty_loans_df():
    df = pd.DataFrame(
        columns=[
            "employee_id",
            "loan_type",
            "amount",
            "interest_rate",
            "loan_term_months",
            "disbursement_date",
            "expected_repayment_date",
            "status",
            "created_at",
        ]
    )
    df = df.astype(
        {
            "disbursement_date": "datetime64[ns]",
            "expected_repayment_date": "datetime64[ns]",
            "created_at": "datetime64[ns]",
            "amount": "float64",
            "interest_rate": "float64",
            "loan_term_months": "int64",
        }
    )
    return df


def load_loans_from_csv():
    if os.path.exists(LOANS_CSV_FILE):
        try:
            df = pd.read_csv(LOANS_CSV_FILE)
            date_cols = ["disbursement_date", "expected_repayment_date", "created_at"]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])

            numeric_cols = ["amount", "interest_rate", "loan_term_months"]

            return df
        except pd.errors.EmptyDataError:
            return initialize_empty_loans_df()
        except Exception as e:
            return initialize_empty_loans_df()
    else:
        return initialize_empty_loans_df()


loans_df = load_loans_from_csv()

loan_salary_app = fastapi.FastAPI()


def check_eligibility_detailed(
    gross_salary: float, pay_frequency: str, requested_advance_amount: float
) -> EligibilityDetails:
    ELIGIBLE_PAY_FREQUENCIES = ["weekly", "bi-weekly", "semi-monthly", "monthly"]
    MIN_SALARY = 200000

    eligibility_details = EligibilityDetails(
        is_eligible=True,
        failed_criteria=[],
        max_eligible_advance=None,
        salary_check=gross_salary >= MIN_SALARY,
        pay_frequency_check=pay_frequency.lower() in ELIGIBLE_PAY_FREQUENCIES,
        amount_check=requested_advance_amount > 0,
        advance_limit_check=True,
    )

    if gross_salary < MIN_SALARY:
        eligibility_details.is_eligible = False
        eligibility_details.salary_check = False
        eligibility_details.failed_criteria.append(
            f"Minimum salary requirement not met. Required: UGX {MIN_SALARY:,.2f}, Your salary: UGX {gross_salary:,.2f}"
        )

    if requested_advance_amount <= 0:
        eligibility_details.is_eligible = False
        eligibility_details.amount_check = False
        eligibility_details.failed_criteria.append(
            "Requested advance amount must be greater than 0"
        )

    if eligibility_details.salary_check and eligibility_details.pay_frequency_check:
        try:
            max_eligible = calculate_advance_amount(gross_salary, pay_frequency)
            eligibility_details.max_eligible_advance = max_eligible

            if requested_advance_amount > max_eligible:
                eligibility_details.is_eligible = False
                eligibility_details.advance_limit_check = False
                eligibility_details.failed_criteria.append(
                    f"Requested amount exceeds maximum eligible advance. Maximum allowed: UGX {max_eligible:,.2f}, Requested: UGX {requested_advance_amount:,.2f}"
                )
        except ValueError as e:
            eligibility_details.is_eligible = False
            eligibility_details.failed_criteria.append(str(e))

    return eligibility_details


@loan_salary_app.post("/calculate_advance", response_model=AdvanceCalculationResponse)
def calculate_salary_advance(request: AdvanceCalculationRequest):
    global loans_df

    gross_salary = request.gross_salary
    pay_frequency = request.pay_frequency
    employee_id = request.employee_id
    requested_amount = request.salary_advance.requested_advance_amount

    eligibility_details = check_eligibility_detailed(
        gross_salary, pay_frequency, requested_amount
    )
    advance_eligible = eligibility_details.is_eligible

    if advance_eligible:
        advance_message = "Eligible for salary advance."
    else:
        advance_message = "Not eligible for salary advance. See details below."

    approved_amount = None
    if advance_eligible:
        approved_amount = requested_amount
        repayment_date = datetime.date.today() + datetime.timedelta(days=30)

        try:
            loans_df = record_loan(
                df_loans=loans_df,
                employee_id=employee_id,
                loan_type="salary_advance",
                amount=approved_amount,
                disbursement_date=datetime.date.today(),
                expected_repayment_date=repayment_date,
                status="approved",
                interest_rate=0.0,
                loan_term_months=0,
            )
            loans_df.to_csv(LOANS_CSV_FILE, index=False)
        except ValueError as e:
            advance_eligible = False
            advance_message = str(e)
            approved_amount = None
            eligibility_details.failed_criteria.append(str(e))

    return AdvanceCalculationResponse(
        error=False,
        error_message="",
        advance_eligible=advance_eligible,
        advance_message=advance_message,
        approved_advance_amount=approved_amount,
        eligibility_details=eligibility_details,
    )


@loan_salary_app.post("/calculate_loan", response_model=LoanCalculationResponse)
def calculate_personal_loan(request: LoanCalculationRequest):
    global loans_df

    employee_id = request.employee_id
    loan_amount = request.loan_amount
    annual_interest_rate = request.annual_interest_rate
    loan_term_months = request.loan_term_months

    try:
        total_repayable = calculate_total_repayable_loan_amount(
            loan_amount, annual_interest_rate, loan_term_months
        )

        schedule_df = generate_amortization_schedule(
            loan_amount, annual_interest_rate, loan_term_months, datetime.date.today()
        )

        amortization_schedule = None
        if not schedule_df.empty:
            amortization_schedule = schedule_df.to_dict(orient="records")

        repayment_date = (
            pd.Timestamp(datetime.date.today()) + pd.DateOffset(months=loan_term_months)
        ).date()

        loans_df = record_loan(
            df_loans=loans_df,
            employee_id=employee_id,
            loan_type="personal_loan",
            amount=loan_amount,
            interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
            disbursement_date=datetime.date.today(),
            expected_repayment_date=repayment_date,
            status="approved",
        )
        loans_df.to_csv(LOANS_CSV_FILE, index=False)

        return LoanCalculationResponse(
            error=False,
            error_message="",
            loan_requested=True,
            loan_total_repayable_amount=total_repayable,
            loan_amortization_schedule=amortization_schedule,
        )

    except ValueError as e:
        return LoanCalculationResponse(
            error=True,
            error_message=str(e),
            loan_requested=False,
            loan_total_repayable_amount=None,
            loan_amortization_schedule=None,
        )


@loan_salary_app.get("/loans", response_model=List[LoanRecord])
def get_all_loans():
    global loans_df

    loans_df = load_loans_from_csv()
    records = loans_df.to_dict(orient="records")
    return records
