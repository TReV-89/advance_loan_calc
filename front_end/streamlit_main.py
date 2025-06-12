import streamlit as st
import requests
import pandas as pd

#FASTAPI_BACKEND_URL = "http://127.0.0.1:8000"
FASTAPI_BACKEND_URL = "http://backend:8000"


def make_request(endpoint, payload):
    """Handle API requests with unified error handling"""
    try:
        response = requests.post(f"{FASTAPI_BACKEND_URL}/{endpoint}", json=payload)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Could not connect to backend at {FASTAPI_BACKEND_URL}"
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def display_result(result, error_msg):
    """Display API result or error message"""
    if error_msg:
        st.error(error_msg)
        return

    if result.get("error"):
        st.error(f"Error: {result.get('error_message', 'Unknown error')}")
        return

    return result


def display_eligibility_details(eligibility_details):
    """Display detailed eligibility criteria with visual indicators"""
    if not eligibility_details:
        return

    st.subheader("📋 Eligibility Criteria Check")

    # Create columns for better layout
    col1, col2 = st.columns([2, 2])

    with col1:
        # Salary check
        if eligibility_details.get("salary_check"):
            st.success("✅ Minimum salary requirement met")
        else:
            st.error("❌ Minimum salary requirement not met")

        # Pay frequency check
        if eligibility_details.get("pay_frequency_check"):
            st.success("✅ Valid pay frequency")
        else:
            st.error("❌ Invalid pay frequency")

        # Amount check
        if eligibility_details.get("amount_check"):
            st.success("✅ Valid advance amount")
        else:
            st.error("❌ Invalid advance amount")

        # Advance limit check
        if eligibility_details.get("advance_limit_check"):
            st.success("✅ Within advance limit")
        else:
            st.error("❌ Exceeds maximum advance limit")

    with col2:
        # Show max eligible amount if available
        max_eligible = eligibility_details.get("max_eligible_advance")
        if max_eligible is not None:
            st.metric(
                "Max Eligible Advance",
                f"UGX {max_eligible:,.2f}",
                help="Maximum advance amount you can request based on your salary",
            )

    # Show failed criteria details
    failed_criteria = eligibility_details.get("failed_criteria", [])
    if failed_criteria:
        st.subheader("❌ Issues to Address:")
        for criterion in failed_criteria:
            st.error(f"• {criterion}")

        # Provide helpful suggestions
        st.subheader("💡 How to Become Eligible:")
        if not eligibility_details.get("salary_check"):
            st.info("• Increase your gross salary to at least UGX 200,000")
        if not eligibility_details.get("advance_limit_check") and max_eligible:
            st.info(
                f"• Reduce your requested advance amount to UGX {max_eligible:,.2f} or less"
            )
        if not eligibility_details.get("pay_frequency_check"):
            st.info(
                "• Ensure your pay frequency is one of: Weekly, Bi-weekly, Semi-monthly, or Monthly"
            )


# App Configuration
st.set_page_config(page_title="Salary Advance & Loan Calculator", layout="centered")
st.title("💰 Salary Advance & Loan Calculator")

# Option Selection
option = st.radio("Select an Option:", ("Get Salary Advance", "Get Personal Loan"))
st.markdown("---")

# Employee Information
st.header("Your Employee Information")
employee_id = st.text_input(
    "Employee ID:", value="EMP001", help="Enter your unique employee identifier."
)

# Salary Advance Section
if option == "Get Salary Advance":
    st.header("📊 Salary Advance Request")

    gross_salary = st.number_input(
        "Gross Salary (UGX):",
        min_value=0.0,
        value=3000000.0,
        step=100000.0,
        format="%.2f",
        help="Your total earnings before taxes and other deductions.",
    )

    pay_frequency = st.selectbox(
        "Pay Frequency:",
        ["Monthly", "Bi-weekly", "Semi-monthly", "Weekly"],
        help="How often you receive your salary.",
    )

    requested_advance_amount = st.number_input(
        "Requested Advance Amount (UGX):",
        min_value=0.0,
        value=500000.0,
        step=50000.0,
        format="%.2f",
        help="The amount of salary advance you wish to take.",
    )

    if st.button("Check Eligibility & Request"):
        if not employee_id:
            st.error("Please enter your Employee ID.")
        else:
            with st.spinner("Processing..."):
                payload = {
                    "gross_salary": gross_salary,
                    "pay_frequency": pay_frequency,
                    "employee_id": employee_id,
                    "salary_advance": {
                        "requested_advance_amount": requested_advance_amount
                    },
                }

                result, error = make_request("calculate_advance", payload)
                result = display_result(result, error)

                if result:
                    # Display eligibility details first
                    eligibility_details = result.get("eligibility_details")
                    display_eligibility_details(eligibility_details)

                    st.markdown("---")
                    st.subheader("🎯 Final Result:")

                    if result.get("advance_eligible"):
                        st.success(f"**Status:** {result.get('advance_message')}")
                        st.write(
                            f"**Approved Amount:** UGX {result.get('approved_advance_amount', 0):,.2f}"
                        )
                        st.info(
                            "🎉 Your salary advance has been processed and recorded!"
                        )

                        # Show next steps
                        st.subheader("📋 Next Steps:")
                        st.write("1. Your advance will be disbursed within 24 hours")
                        st.write("2. The amount will be deducted from your next salary")
                        st.write(
                            "3. Check the 'All Recorded Loans' section below to view details"
                        )
                    else:
                        st.warning(f"**Status:** {result.get('advance_message')}")
                        if eligibility_details and eligibility_details.get(
                            "max_eligible_advance"
                        ):
                            st.info(
                                f"💡 Try requesting up to UGX {eligibility_details['max_eligible_advance']:,.2f} instead"
                            )

# Personal Loan Section
else:
    st.header("🏦 Personal Loan Request")

    loan_amount = st.number_input(
        "Loan Amount (UGX):",
        min_value=0.0,
        value=1000000.0,
        step=100000.0,
        format="%.2f",
        help="The amount of personal loan you wish to take.",
    )

    interest_rate = (
        st.slider(
            "Annual Interest Rate (%):",
            min_value=0.0,
            max_value=25.0,
            value=7.0,
            step=0.1,
            help="The annual interest rate for the personal loan.",
        )
        / 100
    )

    loan_term_months = st.slider(
        "Loan Term (Months):",
        min_value=1,
        max_value=60,
        value=12,
        help="The duration over which you will repay the personal loan.",
    )

    if st.button("Calculate Loan & View Schedule"):
        if not employee_id:
            st.error("Please enter your Employee ID.")
        else:
            with st.spinner("Calculating..."):
                payload = {
                    "employee_id": employee_id,
                    "loan_amount": loan_amount,
                    "annual_interest_rate": interest_rate,
                    "loan_term_months": loan_term_months,
                }

                result, error = make_request("calculate_loan", payload)
                result = display_result(result, error)

                if result and result.get("loan_requested"):
                    st.subheader("Personal Loan Result:")
                    st.success("🎉 Loan calculation successful!")

                    # Display loan summary in metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Loan Amount", f"UGX {loan_amount}")
                    with col2:
                        st.metric("Interest Rate", f"{interest_rate*100:.1f}%")
                    with col3:
                        st.metric("Loan Term", f"{loan_term_months} months")

                    st.write(
                        f"**Total Repayable:** UGX {result.get('loan_total_repayable_amount', 0):,.2f}"
                    )

                    # Display amortization schedule
                    schedule = result.get("loan_amortization_schedule")
                    if schedule:
                        st.write("### 📊 Amortization Schedule")
                        df = pd.DataFrame(schedule)
                        df["Payment_Date"] = pd.to_datetime(df["Payment_Date"])

                        # Format currency columns
                        currency_cols = [
                            "Beginning_Balance",
                            "Monthly_Payment",
                            "Interest_Paid",
                            "Principal_Paid",
                            "Ending_Balance",
                        ]
                        for col in currency_cols:
                            if col in df.columns:
                                df[col] = df[col].apply(lambda x: f"UGX {x:,.2f}")

                        st.dataframe(
                            df.set_index("Payment_Number"), use_container_width=True
                        )

                        # Download button
                        csv = pd.DataFrame(schedule).to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="📥 Download Schedule as CSV",
                            data=csv,
                            file_name=f"amortization_schedule_{employee_id}_{loan_term_months}months.csv",
                            mime="text/csv",
                        )
                    else:
                        st.info("No amortization schedule available.")

# Display All Loans
st.markdown("---")
if st.checkbox("Show All Recorded Loans"):
    try:
        response = requests.get(f"{FASTAPI_BACKEND_URL}/loans")
        response.raise_for_status()
        loans = response.json()

        if loans:
            df = pd.DataFrame(loans)
            # Convert date columns
            date_cols = ["disbursement_date", "expected_repayment_date", "created_at"]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")

            # Format amount column
            if "amount" in df.columns:
                df["amount"] = df["amount"].apply(lambda x: f"UGX {x:,.2f}")

            st.dataframe(df, use_container_width=True)
        else:
            st.info("No loans recorded yet.")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend to fetch loans.")
    except Exception as e:
        st.error(f"Error fetching loans: {e}")
