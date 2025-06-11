import streamlit as st
import requests
import pandas as pd
import datetime

FASTAPI_BACKEND_URL = "http://backend:8000"

# --- Streamlit App Layout ---
st.set_page_config(page_title="Salary Advance & Loan Calculator", layout="centered")

st.title(" Salary Advance & Loan Calculator")
st.markdown("Choose an option below to get started.")

# --- Option Selection ---
option = st.radio(
    "Select an Option:",
    ("Get Salary Advance", "Get Personal Loan"),
    index=0,  # Default to Salary Advance
)

st.markdown("---")  # Separator

# --- Shared Employee ID Input ---
st.header("Your Employee Information")
employee_id = st.text_input(
    "Employee ID:",
    value="EMP001",  # Default value for easy testing
    help="Enter your unique employee identifier.",
)

# --- Salary Advance Form ---
if option == "Get Salary Advance":
    st.header(" Salary Advance Request")

    gross_salary = st.number_input(
        "Gross Salary (UGX, before deductions):",
        min_value=0.0,
        value=3000000.0,
        step=100000.0,
        format="%.2f",
        help="Your total earnings before taxes and other deductions.",
    )

    pay_frequency = st.selectbox(
        "Pay Frequency:",
        options=["Monthly", "Bi-weekly", "Semi-monthly", "Weekly"],
        index=0,
        help="How often you receive your salary.",
    )

    requested_advance_amount = st.number_input(
        "Requested Salary Advance Amount (UGX):",
        min_value=0.0,
        value=500000.0,
        step=50000.0,
        format="%.2f",
        help="The amount of salary advance you wish to take.",
    )

    if st.button("Check Salary Advance Eligibility & Request"):
        if not employee_id:
            st.error("Please enter your Employee ID.")
        else:
            with st.spinner("Processing salary advance request..."):
                payload = {
                    "gross_salary": gross_salary,
                    "pay_frequency": pay_frequency,
                    "employee_id": employee_id,
                    "salary_advance": {
                        "requested_advance_amount": requested_advance_amount
                    },
                }
                try:
                    response = requests.post(
                        f"{FASTAPI_BACKEND_URL}/calculate_advance", json=payload
                    )
                    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                    result = response.json()

                    st.subheader("Salary Advance Result:")
                    if result.get("error"):
                        st.error(
                            f"Error: {result.get('error_message', 'An unknown error occurred.')}"
                        )
                    else:
                        if result.get("advance_eligible"):
                            st.success(
                                f"**Eligibility:** {result.get('advance_message')}"
                            )
                            st.write(
                                f"**Approved Advance Amount:** UGX {result.get('approved_advance_amount', 0.0):,.2f}"
                            )
                            st.write(
                                f"**Advance Fee:** UGX {result.get('advance_fee', 0.0):,.2f}"
                            )

                            st.info(
                                "Your salary advance has been processed and recorded."
                            )
                        else:
                            st.warning(
                                f"**Eligibility:** {result.get('advance_message')}"
                            )

                except requests.exceptions.ConnectionError:
                    st.error(
                        f"Could not connect to the backend at {FASTAPI_BACKEND_URL}. Please ensure it's running."
                    )
                except requests.exceptions.RequestException as e:
                    st.error(f"An error occurred during the request: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")


# --- Personal Loan Form ---
elif option == "Get Personal Loan":
    st.header("🏦 Personal Loan Request")

    loan_amount = st.number_input(
        "Loan Amount (UGX):",
        min_value=0.0,
        value=1000000.0,
        step=100000.0,
        format="%.2f",
        help="The principal amount of the personal loan you are requesting.",
    )

    interest_rate = (
        st.slider(
            "Annual Interest Rate (%):",
            min_value=0.0,
            max_value=25.0,
            value=7.0,
            step=0.1,
            format="%.1f",
            help="The annual interest rate for the personal loan.",
        )
        / 100
    )  # Convert percentage to decimal

    loan_term_months = st.slider(
        "Loan Term (Months):",
        min_value=1,
        max_value=60,
        value=12,
        step=1,
        help="The duration over which you will repay the personal loan.",
    )

    if st.button("Calculate Loan & View Schedule"):
        if not employee_id:
            st.error("Please enter your Employee ID.")
        else:
            with st.spinner("Calculating loan details..."):
                payload = {
                    "employee_id": employee_id,
                    "loan_amount": loan_amount,
                    "annual_interest_rate": interest_rate,
                    "loan_term_months": loan_term_months,
                }
                try:
                    response = requests.post(
                        f"{FASTAPI_BACKEND_URL}/calculate_loan", json=payload
                    )
                    response.raise_for_status()
                    result = response.json()

                    st.subheader("Personal Loan Result:")
                    if result.get("error"):
                        st.error(
                            f"Error: {result.get('error_message', 'An unknown error occurred.')}"
                        )
                    else:
                        if result.get(
                            "loan_requested"
                        ):  # loan_requested indicates successful processing
                            st.success("Loan calculation successful!")
                            st.write(
                                f"**Total Repayable Amount:** UGX {result.get('loan_total_repayable_amount', 0.0):,.2f}"
                            )

                            amortization_schedule = result.get(
                                "loan_amortization_schedule"
                            )
                            if amortization_schedule:
                                st.write("### Amortization Schedule")
                                # Convert list of dicts to DataFrame for display
                                schedule_df = pd.DataFrame(amortization_schedule)
                                # Convert Payment_Date column back to datetime objects for better display in Streamlit
                                schedule_df["Payment_Date"] = pd.to_datetime(
                                    schedule_df["Payment_Date"]
                                )
                                st.dataframe(schedule_df.set_index("Payment_Number"))
                            else:
                                st.info(
                                    "No amortization schedule generated (e.g., for 0-interest or invalid inputs)."
                                )
                        else:
                            st.warning(
                                "Loan request could not be processed."
                            )  # Fallback if loan_requested is False but no specific error_message

                except requests.exceptions.ConnectionError:
                    st.error(
                        f"Could not connect to the backend at {FASTAPI_BACKEND_URL}. Please ensure it's running."
                    )
                except requests.exceptions.RequestException as e:
                    st.error(f"An error occurred during the request: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

st.markdown("---")
st.info(f"Backend API URL: {FASTAPI_BACKEND_URL}")

# Optional: Display all recorded loans from the backend (for debugging)
if st.checkbox("Show All Recorded Loans (for debugging)"):
    try:
        response = requests.get(f"{FASTAPI_BACKEND_URL}/loans")
        response.raise_for_status()
        all_loans = response.json()
        if all_loans:
            loans_df_display = pd.DataFrame(all_loans)
            # Convert date columns back to datetime for better display
            for col in ["disbursement_date", "expected_repayment_date", "created_at"]:
                if col in loans_df_display.columns:
                    loans_df_display[col] = pd.to_datetime(loans_df_display[col])
            st.dataframe(loans_df_display)
        else:
            st.info("No loans recorded yet.")
    except requests.exceptions.ConnectionError:
        st.error(
            f"Could not connect to the backend at {FASTAPI_BACKEND_URL} to fetch loans."
        )
    except Exception as e:
        st.error(f"Error fetching all loans: {e}")
