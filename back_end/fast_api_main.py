import fastapi
import pandas as pd
import datetime
from calculations import (
    record_loan,
    if_eligible,
    calculate_total_repayable_loan_amount,
    generate_amortization_schedule,
    calculate_advance_amount,
)


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
# Ensure correct dtypes for the empty DataFrame
loans_df["disbursement_date"] = pd.to_datetime(loans_df["disbursement_date"])
loans_df["expected_repayment_date"] = pd.to_datetime(
    loans_df["expected_repayment_date"]
)
loans_df["created_at"] = pd.to_datetime(loans_df["created_at"])
loans_df["amount"] = loans_df["amount"].astype(float)
loans_df["interest_rate"] = loans_df["interest_rate"].astype(float)
loans_df["loan_term_months"] = loans_df["loan_term_months"].astype(int)

loan_salary_app = fastapi.FastAPI()

# API Endpoints


@loan_salary_app.post("/calculate_advance")
def calculate_salary_advance(request: dict):
    """
    Calculates salary advance eligibility and records approved advances.
    """
    global loans_df  # Declare that we are modifying the global DataFrame imported from loan_records

    # --- Manual Input Validation for Salary Advance ---
    error_response_template = {
        "error": True,
        "error_message": "",
        "advance_eligible": False,
        "advance_message": "Calculation failed due to invalid input.",
        "approved_advance_amount": None,
    }

    required_salary_info_fields = ["gross_salary", "pay_frequency", "employee_id"]
    for field in required_salary_info_fields:
        if field not in request:
            error_response_template["error_message"] = (
                f"Missing required field: {field}"
            )
            return error_response_template

    gross_salary = request.get("gross_salary")
    pay_frequency = request.get("pay_frequency")
    employee_id = request.get("employee_id")

    if not isinstance(gross_salary, (int, float)) or gross_salary <= 0:
        error_response_template["error_message"] = (
            "gross_salary must be a positive number."
        )
        return error_response_template
    if not isinstance(pay_frequency, str):
        error_response_template["error_message"] = "pay_frequency must be a string."
        return error_response_template
    if not isinstance(employee_id, str) or not employee_id:
        error_response_template["error_message"] = (
            "employee_id must be a non-empty string."
        )
        return error_response_template

    # Salary Advance Request specific validation
    if "salary_advance" not in request:
        error_response_template["error_message"] = "Missing 'salary_advance' details."
        return error_response_template
    salary_advance_req = request["salary_advance"]
    if "requested_advance_amount" not in salary_advance_req:
        error_response_template["error_message"] = (
            "Missing 'requested_advance_amount' in salary_advance."
        )
        return error_response_template
    requested_advance_amount = salary_advance_req.get("requested_advance_amount")
    if (
        not isinstance(requested_advance_amount, (int, float))
        or requested_advance_amount <= 0
    ):
        error_response_template["error_message"] = (
            "requested_advance_amount must be a positive number."
        )
        return error_response_template

    # --- Salary Advance Calculation ---
    advance_eligible = if_eligible(
        gross_salary=gross_salary,
        pay_frequency=pay_frequency,
        requested_advance_amount=requested_advance_amount,
    )
    advance_message = (
        "Eligible for salary advance."
        if advance_eligible
        else "Not eligible for salary advance based on criteria."
    )

    approved_advance_amount = None

    if advance_eligible:
        approved_advance_amount = requested_advance_amount

        temp_expected_repayment_date = datetime.date.today() + datetime.timedelta(
            days=30
        )

        try:
            loans_df = record_loan(
                df_loans=loans_df,
                employee_id=employee_id,
                loan_type="salary_advance",
                amount=approved_advance_amount,
                disbursement_date=datetime.date.today(),
                expected_repayment_date=temp_expected_repayment_date,  # Use temp variable for record_loan
                status="approved",
                interest_rate=0.0,  # Salary advances typically have 0 interest
                loan_term_months=0,  # Salary advances typically have 0 term
            )
        except ValueError as e:
            advance_eligible = False
            advance_message = str(e)
            approved_advance_amount = None

    return {
        "error": False,
        "error_message": "",
        "advance_eligible": advance_eligible,
        "advance_message": advance_message,
        "approved_advance_amount": approved_advance_amount,
    }


@loan_salary_app.post("/calculate_loan")
def calculate_personal_loan(request: dict):
    """
    Calculates personal loan details (total repayable, amortization schedule) and records approved loans.
    """
    global loans_df  # Declare that we are modifying the global DataFrame imported from loan_records

    # --- Manual Input Validation for Personal Loan ---
    error_response_template = {
        "error": True,
        "error_message": "",
        "loan_requested": False,  # Renamed from original personal_loan_req check
        "loan_total_repayable_amount": None,
        "loan_amortization_schedule": None,
    }

    required_loan_fields = [
        "employee_id",
        "loan_amount",
        "annual_interest_rate",
        "loan_term_months",
    ]
    for field in required_loan_fields:
        if field not in request:
            error_response_template["error_message"] = (
                f"Missing required field: {field}"
            )
            return error_response_template

    employee_id = request.get("employee_id")
    loan_amount = request.get("loan_amount")
    annual_interest_rate = request.get("annual_interest_rate")
    loan_term_months = request.get("loan_term_months")

    if not isinstance(employee_id, str) or not employee_id:
        error_response_template["error_message"] = (
            "employee_id must be a non-empty string."
        )
        return error_response_template
    if not isinstance(loan_amount, (int, float)) or loan_amount <= 0:
        error_response_template["error_message"] = (
            "loan_amount must be a positive number."
        )
        return error_response_template
    if not isinstance(annual_interest_rate, (int, float)) or not (
        0 <= annual_interest_rate <= 1.0
    ):
        error_response_template["error_message"] = (
            "annual_interest_rate must be a number between 0 and 1.0."
        )
        return error_response_template
    if not isinstance(loan_term_months, int) or loan_term_months <= 0:
        error_response_template["error_message"] = (
            "loan_term_months must be a positive integer."
        )
        return error_response_template

    # --- Personal Loan Calculation ---
    loan_total_repayable_amount = None
    loan_amortization_schedule = None
    loan_requested = True  # Assume loan is requested if input is valid

    try:
        loan_total_repayable_amount = calculate_total_repayable_loan_amount(
            principal_amount=loan_amount,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
        )

        schedule_df = generate_amortization_schedule(
            principal_amount=loan_amount,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
            start_date=datetime.date.today(),
        )
        if not schedule_df.empty:
            loan_amortization_schedule = schedule_df.to_dict(orient="records")
            for entry in loan_amortization_schedule:
                if isinstance(entry.get("Payment_Date"), datetime.date):
                    entry["Payment_Date"] = entry["Payment_Date"].isoformat()

        # Record the personal loan
        loans_df = record_loan(
            df_loans=loans_df,
            employee_id=employee_id,
            loan_type="personal_loan",
            amount=loan_amount,
            interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
            disbursement_date=datetime.date.today(),
            expected_repayment_date=(
                pd.Timestamp(datetime.date.today())
                + pd.DateOffset(months=loan_term_months)
            ).date(),  # Set based on term
            status="approved",
        )
    except ValueError as e:
        loan_requested = False
        loan_total_repayable_amount = None
        loan_amortization_schedule = None
        error_response_template["error_message"] = str(e)
        return error_response_template

    return {
        "error": False,
        "error_message": "",
        "loan_requested": loan_requested,
        "loan_total_repayable_amount": loan_total_repayable_amount,
        "loan_amortization_schedule": loan_amortization_schedule,
    }


@loan_salary_app.get("/loans")
def get_all_loans():
    """
    Returns all recorded loans for debugging/demonstration purposes.
    """
    records = loans_df.to_dict(orient="records")
    for record in records:
        if isinstance(record.get("disbursement_date"), datetime.date):
            record["disbursement_date"] = record["disbursement_date"].isoformat()
        if isinstance(record.get("expected_repayment_date"), datetime.date):
            record["expected_repayment_date"] = record[
                "expected_repayment_date"
            ].isoformat()
        if isinstance(record.get("created_at"), datetime.datetime):
            record["created_at"] = record["created_at"].isoformat()
    return records
