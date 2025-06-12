import fastapi
import pandas as pd
import datetime
from calculations import (
    record_loan,
    if_eligible,
    calculate_advance_amount,
    calculate_total_repayable_loan_amount,
    generate_amortization_schedule,
)

# Initialize loans DataFrame
loans_df = pd.DataFrame(
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

# Set correct dtypes
loans_df = loans_df.astype(
    {
        "disbursement_date": "datetime64[ns]",
        "expected_repayment_date": "datetime64[ns]",
        "created_at": "datetime64[ns]",
        "amount": "float64",
        "interest_rate": "float64",
        "loan_term_months": "int64",
    }
)

loan_salary_app = fastapi.FastAPI()


def validate_common_fields(request: dict, required_fields: list) -> tuple:
    """Validate common request fields and return error if any"""
    for field in required_fields:
        if field not in request:
            return True, f"Missing required field: {field}"
    return False, None


def serialize_dates(record: dict) -> dict:
    """Convert date objects to ISO format strings"""
    date_fields = ["disbursement_date", "expected_repayment_date", "created_at"]
    for field in date_fields:
        if field in record and isinstance(
            record[field], (datetime.date, datetime.datetime)
        ):
            record[field] = record[field].isoformat()
    return record


def check_eligibility_detailed(
    gross_salary: float, pay_frequency: str, requested_advance_amount: float
) -> dict:
    """Check eligibility with detailed feedback on each criterion"""
    ELIGIBLE_PAY_FREQUENCIES = ["weekly", "bi-weekly", "semi-monthly", "monthly"]
    MIN_SALARY = 200000

    eligibility_details = {
        "is_eligible": True,
        "failed_criteria": [],
        "max_eligible_advance": None,
        "salary_check": gross_salary >= MIN_SALARY,
        "pay_frequency_check": pay_frequency.lower() in ELIGIBLE_PAY_FREQUENCIES,
        "amount_check": requested_advance_amount > 0,
        "advance_limit_check": True,
    }

    # Check minimum salary
    if gross_salary < MIN_SALARY:
        eligibility_details["is_eligible"] = False
        eligibility_details["salary_check"] = False
        eligibility_details["failed_criteria"].append(
            f"Minimum salary requirement not met. Required: UGX {MIN_SALARY:,.2f}, Your salary: UGX {gross_salary:,.2f}"
        )

    # Check pay frequency
    if pay_frequency.lower() not in ELIGIBLE_PAY_FREQUENCIES:
        eligibility_details["is_eligible"] = False
        eligibility_details["pay_frequency_check"] = False
        eligibility_details["failed_criteria"].append(
            f"Invalid pay frequency. Supported frequencies: {', '.join(ELIGIBLE_PAY_FREQUENCIES)}"
        )

    # Check requested amount is positive
    if requested_advance_amount <= 0:
        eligibility_details["is_eligible"] = False
        eligibility_details["amount_check"] = False
        eligibility_details["failed_criteria"].append(
            "Requested advance amount must be greater than 0"
        )

    # Check advance limit (only if other checks pass)
    if (
        eligibility_details["salary_check"]
        and eligibility_details["pay_frequency_check"]
    ):
        try:
            max_eligible = calculate_advance_amount(gross_salary, pay_frequency)
            eligibility_details["max_eligible_advance"] = max_eligible

            if requested_advance_amount > max_eligible:
                eligibility_details["is_eligible"] = False
                eligibility_details["advance_limit_check"] = False
                eligibility_details["failed_criteria"].append(
                    f"Requested amount exceeds maximum eligible advance. Maximum allowed: UGX {max_eligible:,.2f}, Requested: UGX {requested_advance_amount:,.2f}"
                )
        except ValueError as e:
            eligibility_details["is_eligible"] = False
            eligibility_details["failed_criteria"].append(str(e))

    return eligibility_details


@loan_salary_app.post("/calculate_advance")
def calculate_salary_advance(request: dict):
    """Calculate salary advance eligibility and record approved advances"""
    global loans_df

    # Validation
    error, msg = validate_common_fields(
        request, ["gross_salary", "pay_frequency", "employee_id"]
    )
    if error:
        return {
            "error": True,
            "error_message": msg,
            "advance_eligible": False,
            "advance_message": "Calculation failed",
            "approved_advance_amount": None,
            "eligibility_details": None,
        }

    # Extract and validate salary advance data
    if (
        "salary_advance" not in request
        or "requested_advance_amount" not in request["salary_advance"]
    ):
        return {
            "error": True,
            "error_message": "Missing salary_advance details",
            "advance_eligible": False,
            "advance_message": "Calculation failed",
            "approved_advance_amount": None,
            "eligibility_details": None,
        }

    gross_salary = request["gross_salary"]
    pay_frequency = request["pay_frequency"]
    employee_id = request["employee_id"]
    requested_amount = request["salary_advance"]["requested_advance_amount"]

    # Basic type validation
    if not isinstance(gross_salary, (int, float)) or gross_salary <= 0:
        return {
            "error": True,
            "error_message": "Invalid gross_salary",
            "advance_eligible": False,
            "advance_message": "Calculation failed",
            "approved_advance_amount": None,
            "eligibility_details": None,
        }

    if not isinstance(requested_amount, (int, float)) or requested_amount <= 0:
        return {
            "error": True,
            "error_message": "Invalid requested_advance_amount",
            "advance_eligible": False,
            "advance_message": "Calculation failed",
            "approved_advance_amount": None,
            "eligibility_details": None,
        }

    # Check detailed eligibility
    eligibility_details = check_eligibility_detailed(
        gross_salary, pay_frequency, requested_amount
    )
    advance_eligible = eligibility_details["is_eligible"]

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
        except ValueError as e:
            advance_eligible = False
            advance_message = str(e)
            approved_amount = None
            eligibility_details["failed_criteria"].append(str(e))

    return {
        "error": False,
        "error_message": "",
        "advance_eligible": advance_eligible,
        "advance_message": advance_message,
        "approved_advance_amount": approved_amount,
        "eligibility_details": eligibility_details,
    }


@loan_salary_app.post("/calculate_loan")
def calculate_personal_loan(request: dict):
    """Calculate personal loan details and record approved loans"""
    global loans_df

    # Validation
    required_fields = [
        "employee_id",
        "loan_amount",
        "annual_interest_rate",
        "loan_term_months",
    ]
    error, msg = validate_common_fields(request, required_fields)
    if error:
        return {
            "error": True,
            "error_message": msg,
            "loan_requested": False,
            "loan_total_repayable_amount": None,
            "loan_amortization_schedule": None,
        }

    employee_id = request["employee_id"]
    loan_amount = request["loan_amount"]
    annual_interest_rate = request["annual_interest_rate"]
    loan_term_months = request["loan_term_months"]

    # Basic validation
    if (
        not isinstance(loan_amount, (int, float))
        or loan_amount <= 0
        or not isinstance(annual_interest_rate, (int, float))
        or not (0 <= annual_interest_rate <= 1.0)
        or not isinstance(loan_term_months, int)
        or loan_term_months <= 0
    ):
        return {
            "error": True,
            "error_message": "Invalid loan parameters",
            "loan_requested": False,
            "loan_total_repayable_amount": None,
            "loan_amortization_schedule": None,
        }

    try:
        # Calculate loan details
        total_repayable = calculate_total_repayable_loan_amount(
            loan_amount, annual_interest_rate, loan_term_months
        )

        schedule_df = generate_amortization_schedule(
            loan_amount, annual_interest_rate, loan_term_months, datetime.date.today()
        )

        amortization_schedule = None
        if not schedule_df.empty:
            amortization_schedule = schedule_df.to_dict(orient="records")
            for entry in amortization_schedule:
                entry = serialize_dates(entry)

        # Record the loan
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

        return {
            "error": False,
            "error_message": "",
            "loan_requested": True,
            "loan_total_repayable_amount": total_repayable,
            "loan_amortization_schedule": amortization_schedule,
        }

    except ValueError as e:
        return {
            "error": True,
            "error_message": str(e),
            "loan_requested": False,
            "loan_total_repayable_amount": None,
            "loan_amortization_schedule": None,
        }


@loan_salary_app.get("/loans")
def get_all_loans():
    """Return all recorded loans"""
    records = loans_df.to_dict(orient="records")
    return [serialize_dates(record) for record in records]
