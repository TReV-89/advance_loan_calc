import pandas as pd
import datetime
import math


def calculate_advance_amount(gross_salary: float, pay_frequency: str) -> int:
    """Calculate maximum advance limit based on monthly gross salary."""
    frequency_multipliers = {
        "weekly": 4,
        "bi-weekly": 2,
        "semi-monthly": 2,
        "monthly": 1,
    }

    multiplier = frequency_multipliers.get(pay_frequency.lower())
    if not multiplier:
        raise ValueError(
            "Unsupported pay frequency. Use: weekly, bi-weekly, semi-monthly, monthly."
        )

    monthly_gross = gross_salary * multiplier
    return int(monthly_gross * 0.5)


def if_eligible(
    gross_salary: float, pay_frequency: str, requested_advance_amount: float
) -> bool:
    """Check if user is eligible for a loan based on salary and request."""
    if gross_salary < 200000 or requested_advance_amount <= 0:
        return False

    try:
        max_eligible = calculate_advance_amount(gross_salary, pay_frequency)
        return requested_advance_amount <= max_eligible
    except ValueError:
        return False


def record_loan(
    df_loans: pd.DataFrame,
    employee_id: str,
    loan_type: str,
    amount: float,
    disbursement_date: datetime.date,
    expected_repayment_date: datetime.date,
    interest_rate: float = 0.0,
    loan_term_months: int = 0,
    status: str = "approved",
) -> pd.DataFrame:
    """Record a new loan, ensuring one active loan per employee."""

    columns = [
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

    # Initialize empty DataFrame with proper schema
    if df_loans.empty:
        df_loans = pd.DataFrame(columns=columns)
        for col in ["disbursement_date", "expected_repayment_date", "created_at"]:
            df_loans[col] = pd.to_datetime(df_loans[col])
        df_loans["amount"] = df_loans["amount"].astype(float)
        df_loans["interest_rate"] = df_loans["interest_rate"].astype(float)
        df_loans["loan_term_months"] = df_loans["loan_term_months"].astype(int)

    # Check for existing active loans
    active_loans = df_loans[
        (df_loans["employee_id"] == employee_id)
        & (df_loans["status"].isin(["approved", "disbursed"]))
    ]
    if not active_loans.empty:
        raise ValueError(f"Employee {employee_id} already has an active loan.")

    # Set default dates
    disbursement_date = disbursement_date or datetime.date.today()
    expected_repayment_date = expected_repayment_date or (
        disbursement_date + datetime.timedelta(days=30)
    )

    new_record = {
        "employee_id": employee_id,
        "loan_type": loan_type,
        "amount": amount,
        "interest_rate": interest_rate,
        "loan_term_months": loan_term_months,
        "disbursement_date": pd.to_datetime(disbursement_date),
        "expected_repayment_date": pd.to_datetime(expected_repayment_date),
        "status": status,
        "created_at": pd.to_datetime(datetime.datetime.now()),
    }

    df_loans = pd.concat([df_loans, pd.DataFrame([new_record])], ignore_index=True)
    print(f"Loan recorded successfully for employee {employee_id}.")
    return df_loans


def calculate_total_repayable_loan_amount(
    principal_amount: float, annual_interest_rate: float, loan_term_months: int
) -> int:
    """Calculate total repayable amount with compound interest (monthly compounding)."""
    if principal_amount <= 0 or annual_interest_rate < 0 or loan_term_months <= 0:
        print("Error: Invalid input parameters.")
        return 0

    # Compound Interest: A = P * (1 + r/n)^(n*t)
    n = 12 
    t_years = loan_term_months / n
    total_amount = principal_amount * math.pow(
        (1 + annual_interest_rate / n), (n * t_years)
    )

    return int(total_amount)


def generate_amortization_schedule(
    principal_amount: float,
    annual_interest_rate: float,
    loan_term_months: int,
    start_date: datetime.date,
) -> pd.DataFrame:
    """Generate detailed loan amortization schedule."""
    if principal_amount <= 0 or annual_interest_rate < 0 or loan_term_months <= 0:
        print("Error: Invalid input parameters.")
        return pd.DataFrame()

    start_date = start_date or datetime.date.today()
    monthly_interest_rate = annual_interest_rate / 12

    # Calculate monthly payment
    if annual_interest_rate == 0:
        monthly_payment = principal_amount / loan_term_months
    else:
        try:
            factor = math.pow(1 + monthly_interest_rate, loan_term_months)
            monthly_payment = (
                principal_amount * (monthly_interest_rate * factor) / (factor - 1)
            )
        except ZeroDivisionError:
            print("Error: Calculation resulted in division by zero.")
            return pd.DataFrame()

    schedule_data = []
    remaining_balance = principal_amount

    for i in range(1, loan_term_months + 1):
        beginning_balance = remaining_balance
        interest_paid = beginning_balance * monthly_interest_rate

        if i == loan_term_months:  # Last payment
            principal_paid = beginning_balance
            monthly_payment = beginning_balance + interest_paid
        else:
            principal_paid = monthly_payment - interest_paid

        remaining_balance = max(0, remaining_balance - principal_paid)
        payment_date = start_date + pd.DateOffset(months=i - 1)

        schedule_data.append(
            {
                "Payment_Number": i,
                "Payment_Date": payment_date.strftime("%Y-%m-%d"),
                "Beginning_Balance": round(beginning_balance, 2),
                "Monthly_Payment": round(monthly_payment, 2),
                "Interest_Paid": round(interest_paid, 2),
                "Principal_Paid": round(principal_paid, 2),
                "Ending_Balance": round(remaining_balance, 2),
            }
        )

    df_schedule = pd.DataFrame(schedule_data)
    df_schedule["Payment_Number"] = df_schedule["Payment_Number"].astype(int)
    df_schedule["Payment_Date"] = pd.to_datetime(df_schedule["Payment_Date"])

    return df_schedule
