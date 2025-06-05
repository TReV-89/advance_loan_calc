import pandas as pd
import datetime
import math


def calculate_advance_amount(
    gross_salary: float, pay_frequency: str, requested_advance_amount: float
) -> int:
    # --- Rule 4: Calculate Maximum Advance Limit based on Monthly Gross ---
    # Convert gross salary to a monthly equivalent for consistent calculation
    monthly_gross_salary = 0.0
    if pay_frequency.lower() == "weekly":
        monthly_gross_salary = gross_salary * 4  # Approximately 4 weeks in a month
    elif pay_frequency.lower() == "bi-weekly":
        monthly_gross_salary = (
            gross_salary * 2
        )  # Approximately 2 bi-weekly periods in a month
    elif pay_frequency.lower() == "semi-monthly":
        monthly_gross_salary = gross_salary * 2
    elif pay_frequency.lower() == "monthly":
        monthly_gross_salary = gross_salary
    else:
        # This case should ideally be caught by Rule 2, but as a fallback
        raise ValueError(
            "Unsupported pay frequency. Supported frequencies are: weekly, bi-weekly, semi-monthly, monthly."
        )

    max_eligible_advance = monthly_gross_salary * 0.5
    return int(max_eligible_advance)


def if_eligible(
    gross_salary: float, pay_frequency: str, requested_advance_amount: float
) -> bool:
    """
    Function to check if the user is eligible for a loan based on their salary.
    This is a placeholder function and should be replaced with actual logic.
    """
    ELIGIBLE_PAY_FREQUENCIES = ["weekly", "bi-weekly", "semi-monthly", "monthly"]
    # --- Rule 1: Validate Gross Salary ---
    if gross_salary < 500000:

        return False

    # --- Rule 2: Validate Pay Frequency ---
    if pay_frequency.lower() not in ELIGIBLE_PAY_FREQUENCIES:

        return False
    # --- Rule 3: Validate Requested Advance Amount ---
    if requested_advance_amount <= 0:

        return False
    # --- Rule 4: Calculate Maximum Advance Limit based on Monthly Gross ---
    # Convert gross salary to a monthly equivalent for consistent calculation
    max_eligible_advance = calculate_advance_amount(
        gross_salary, pay_frequency, requested_advance_amount
    )

    if requested_advance_amount > max_eligible_advance:

        return False

    # --- All checks passed ---

    return True


def record_loan(
    df_loans: pd.DataFrame,
    employee_id: str,
    loan_type: str,  # e.g., 'salary_advance', 'personal_loan'
    amount: float,
    disbursement_date: datetime.date,  # Defaults to today if not provided
    expected_repayment_date: datetime.date,  # Primarily for salary advances
    interest_rate: float = 0.0,  # Applicable for personal loans, 0 for advances
    loan_term_months: int = 0,  # Applicable for personal loans, 0 for advances
    status: str = "approved",
) -> pd.DataFrame:  # Changed return type to include a message
    """
    Records a new loan or salary advance into a Pandas DataFrame.
    Limits an employee to one active loan at a time (status 'approved' or 'disbursed').

    If the DataFrame is empty or new, it initializes it with the correct schema.
    Otherwise, it appends the new loan record.

    """

    # Define the schema for the loans DataFrame
    column_names = [
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

    # If the input DataFrame is empty or doesn't have the correct columns, initialize it
    if df_loans.empty:
        df_loans = pd.DataFrame(columns=column_names)
        # Explicitly set datetime dtypes for empty columns
        df_loans["disbursement_date"] = pd.to_datetime(df_loans["disbursement_date"])
        df_loans["expected_repayment_date"] = pd.to_datetime(
            df_loans["expected_repayment_date"]
        )
        df_loans["created_at"] = pd.to_datetime(df_loans["created_at"])
        # Explicitly set numerical dtypes for empty columns
        df_loans["amount"] = df_loans["amount"].astype(float)
        df_loans["interest_rate"] = df_loans["interest_rate"].astype(float)
        df_loans["loan_term_months"] = df_loans["loan_term_months"].astype(int)

    # --- NEW RULE: Check for existing active loans for the employee ---
    active_statuses = ["approved", "disbursed"]
    employee_active_loans = df_loans[
        (df_loans["employee_id"] == employee_id)
        & (df_loans["status"].isin(active_statuses))
    ]

    if not employee_active_loans.empty:
        raise ValueError(
            f"Employee {employee_id} already has an active loan. Cannot take out another loan.",
        )
    # --- END NEW RULE ---

    # Set default dates if not provided
    if disbursement_date is None:
        disbursement_date = datetime.date.today()
    if expected_repayment_date is None:
        # Default for advances: next month's 1st or 15th, for simplicity let's say 1 month from now
        expected_repayment_date = disbursement_date + datetime.timedelta(days=30)

    # Create a new record as a dictionary
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

    # Append the new record to the DataFrame
    df_loans = pd.concat([df_loans, pd.DataFrame([new_record])], ignore_index=True)

    print(f"Loan recorded successfully for employee {employee_id}.")
    return df_loans


def calculate_total_repayable_loan_amount(
    principal_amount: float, annual_interest_rate: float, loan_term_months: int
) -> int:
    """
    Calculates the total repayable amount for a loan, including compound interest.
    Assumes monthly compounding.


    """

    # Input validation
    if principal_amount <= 0:
        print("Error: Principal amount must be positive.")
        return 0
    if annual_interest_rate < 0:
        print("Error: Annual interest rate cannot be negative.")
        return 0
    if loan_term_months <= 0:
        print("Error: Loan term in months must be positive.")
        return 0

    # Convert annual interest rate to monthly interest rate
    # r_monthly = annual_interest_rate / 12
    # Number of times interest is compounded per year (n) for monthly compounding
    n = 12

    # Convert loan term from months to years
    t_years = loan_term_months / n

    # Compound Interest Formula: A = P * (1 + r/n)^(n*t)
    # A = Total amount after interest
    # P = Principal amount
    # r = Annual interest rate (decimal)
    # n = Number of times interest is compounded per year
    # t = Time in years

    # Calculate the total repayable amount
    total_repayable_amount = principal_amount * math.pow(
        (1 + annual_interest_rate / n), (n * t_years)
    )

    return int(total_repayable_amount)


def generate_amortization_schedule(
    principal_amount: float,
    annual_interest_rate: float,  # e.g., 0.05 for 5%
    loan_term_months: int,
    start_date: datetime.date,  # Optional start date for the schedule
) -> pd.DataFrame:
    """
    Generates a detailed loan amortization schedule using Pandas.

    """

    # --- Input Validation ---
    if principal_amount <= 0:
        print("Error: Principal amount must be positive.")
        return pd.DataFrame()
    if annual_interest_rate < 0:
        print("Error: Annual interest rate cannot be negative.")
        return pd.DataFrame()
    if loan_term_months <= 0:
        print("Error: Loan term in months must be positive.")
        return pd.DataFrame()

    if start_date is None:
        start_date = datetime.date.today()

    # --- Calculate Monthly Interest Rate and Monthly Payment ---
    # Convert annual interest rate to monthly interest rate
    # If interest rate is 0, handle separately to avoid division by zero or log(1) issues
    if annual_interest_rate == 0:
        monthly_interest_rate = 0.0
        # If no interest, monthly payment is just principal / term
        monthly_payment = principal_amount / loan_term_months
    else:
        monthly_interest_rate = annual_interest_rate / 12

        # Formula for fixed monthly payment (M):
        # M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1]
        # P = Principal, i = monthly interest rate, n = total number of payments (loan_term_months)
        try:
            monthly_payment = (
                principal_amount
                * (
                    monthly_interest_rate
                    * math.pow(1 + monthly_interest_rate, loan_term_months)
                )
                / (math.pow(1 + monthly_interest_rate, loan_term_months) - 1)
            )
        except ZeroDivisionError:
            print("Error: Calculation resulted in division by zero. Check inputs.")
            return pd.DataFrame()

    # --- Initialize Amortization Schedule Data ---
    schedule_data = []
    remaining_balance = principal_amount

    # --- Generate Schedule ---
    for i in range(1, loan_term_months + 1):
        beginning_balance = remaining_balance

        # Calculate interest paid for this month
        interest_paid = beginning_balance * monthly_interest_rate

        # Calculate principal paid for this month
        # For the last payment, adjust principal paid to clear remaining balance
        # to account for potential floating point inaccuracies.
        if i == loan_term_months:
            principal_paid = beginning_balance  # Pay off the exact remaining balance
            monthly_payment = beginning_balance + interest_paid  # Adjust last payment
        else:
            principal_paid = monthly_payment - interest_paid

        # Update remaining balance
        remaining_balance -= principal_paid

        # Ensure remaining balance doesn't go negative due to floating point errors
        if (
            remaining_balance < 0.0001 and i == loan_term_months
        ):  # Allow for tiny residual
            remaining_balance = 0.0
        elif (
            remaining_balance < 0
        ):  # If it goes significantly negative before last payment, something is wrong
            print(
                f"Warning: Remaining balance went negative before last payment. Payment {i}. Balance: {remaining_balance}"
            )
            remaining_balance = 0.0  # Cap at zero

        # Determine payment date
        # Add 'i-1' months to the start_date for payment date
        payment_date = start_date + pd.DateOffset(months=i - 1)

        schedule_data.append(
            {
                "Payment_Number": i,
                "Payment_Date": payment_date.strftime(
                    "%Y-%m-%d"
                ),  # Format date as string
                "Beginning_Balance": beginning_balance,
                "Monthly_Payment": monthly_payment,
                "Interest_Paid": interest_paid,
                "Principal_Paid": principal_paid,
                "Ending_Balance": remaining_balance,
            }
        )

    # Create DataFrame from schedule data
    df_schedule = pd.DataFrame(schedule_data)

    # --- Type Casting for DataFrame Columns ---
    df_schedule["Payment_Number"] = df_schedule["Payment_Number"].astype(int)
    # Convert 'Payment_Date' column to datetime objects
    df_schedule["Payment_Date"] = pd.to_datetime(df_schedule["Payment_Date"])
    df_schedule["Beginning_Balance"] = (
        df_schedule["Beginning_Balance"].astype(float).round(2)
    )
    df_schedule["Monthly_Payment"] = (
        df_schedule["Monthly_Payment"].astype(float).round(2)
    )
    df_schedule["Interest_Paid"] = df_schedule["Interest_Paid"].astype(float).round(2)
    df_schedule["Principal_Paid"] = df_schedule["Principal_Paid"].astype(float).round(2)
    df_schedule["Ending_Balance"] = df_schedule["Ending_Balance"].astype(float).round(2)

    return df_schedule
