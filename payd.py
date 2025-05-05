import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from openai import OpenAI

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- Global Design Polish ---
st.markdown("""
<style>
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        font-size: 15px;
    }
    h1, h2, h3, h4 {
        font-weight: 600;
    }
    .block-container {
        padding: 2rem 3rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        padding: 1rem 1.5rem;
    }
    .stMetric label {
        font-weight: 600;
    }
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Tabs (safe for all platforms) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Step 1: Income & Deductions",
    "Step 2: Expenses",
    "Step 3: Credit Cards",
    "Step 4: Results"
])

with tab1:
    st.subheader("Income & Deductions")
    col1, col2 = st.columns([2, 1])
    with col1:
        salary = st.number_input("Annual Gross Salary ($)", min_value=0, value=45000, step=1000)
        state_tax = st.slider("State Tax Rate", 0, 15, 6, step=1) / 100
        fed_tax = st.slider("Federal Tax Rate", 0, 37, 12, step=1) / 100
        retirement_pct = st.slider("401(k) Contribution", 0, 20, 5, step=1) / 100

    with col2:
        health_insurance = st.number_input("Health Insurance Deduction ($)", min_value=0, value=300, step=25)
        retirement_contrib = salary * retirement_pct
        taxable_salary = salary - retirement_contrib
        ss_tax = min(taxable_salary, 168600) * 0.062
        medicare_tax = taxable_salary * 0.0145
        federal_tax = taxable_salary * fed_tax
        state_tax_amt = taxable_salary * state_tax

        total_monthly_deductions = sum([
            federal_tax / 12,
            state_tax_amt / 12,
            ss_tax / 12,
            medicare_tax / 12,
            retirement_contrib / 12,
            health_insurance
        ])

        monthly_net_income = (salary - federal_tax - state_tax_amt - ss_tax - medicare_tax - retirement_contrib) / 12 - health_insurance
        income_after_expenses = monthly_net_income

        st.markdown("#### Monthly Deductions Summary")
        st.markdown(f"""
        <div style='background-color: #f9f9f9; padding: 1rem; border-radius: 10px; border: 1px solid #ddd;'>
            <b>Federal Tax:</b> ${federal_tax / 12:,.2f}<br>
            <b>State Tax:</b> ${state_tax_amt / 12:,.2f}<br>
            <b>Social Security:</b> ${ss_tax / 12:,.2f}<br>
            <b>Medicare:</b> ${medicare_tax / 12:,.2f}<br>
            <b>401(k):</b> ${retirement_contrib / 12:,.2f}<br>
            <b>Health Insurance:</b> ${health_insurance:,.2f}<br>
            <hr>
            <h4 style='color: #d32f2f;'>${total_monthly_deductions:,.2f} / mo</h4>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("Monthly Expenses")
    if "expenses" not in st.session_state:
        st.session_state.expenses = {}
    with st.form("expense_form", clear_on_submit=True):
        exp_name = st.text_input("Expense Name")
        exp_amt = st.number_input("Amount ($)", min_value=0, step=50)
        if st.form_submit_button("Add Expense") and exp_name:
            st.session_state.expenses[exp_name] = exp_amt

    if st.session_state.expenses:
        exp_df = pd.DataFrame(st.session_state.expenses.items(), columns=["Expense", "Amount"])
        st.dataframe(exp_df, use_container_width=True)
    total_expenses = sum(st.session_state.expenses.values())
    st.markdown(f"**Total Monthly Expenses:** `${total_expenses:,.2f}`")
    credit_spend_pct = st.slider("% of expenses on credit cards", 0, 100, 50, step=5) / 100
    income_after_expenses -= total_expenses

with tab3:
    st.subheader("Credit Cards")
    if "cards" not in st.session_state:
        st.session_state.cards = {}
    with st.form("card_form", clear_on_submit=True):
        card_name = st.text_input("Card Name")
        card_bal = st.number_input("Card Balance ($)", min_value=0, step=50)
        card_apr = st.number_input("Card APR (%)", min_value=0.0, step=0.1)
        if st.form_submit_button("Add Card") and card_name:
            st.session_state.cards[card_name] = {"balance": card_bal, "apr": card_apr / 100}

    if st.session_state.cards:
        card_df = pd.DataFrame([
            {"Card": k, "Balance": v["balance"], "APR": f"{v['apr'] * 100:.2f}%"} for k, v in st.session_state.cards.items()
        ])
        st.dataframe(card_df, use_container_width=True)

with tab4:
    st.subheader("Results & Strategy")
    reserve_pct = st.slider("% of leftover income to reserve", 0, 50, 20, step=5) / 100
    credit_contribution = income_after_expenses * (1 - reserve_pct)
    monthly_credit_reuse = total_expenses * credit_spend_pct
    net_reduction = credit_contribution - monthly_credit_reuse

    total_balance = sum(c["balance"] for c in st.session_state.cards.values())
    weighted_apr = sum(c["balance"] * c["apr"] for c in st.session_state.cards.values()) / total_balance if total_balance else 0
    monthly_rate = weighted_apr / 12

    balance = total_balance
    months = 0
    balances = []
    while balance > 0 and months < 600:
        interest = balance * monthly_rate
        balance += interest + monthly_credit_reuse - credit_contribution
        balances.append(balance)
        if balance > total_balance * 10:
            break
        months += 1

    if balance <= 0:
        st.success(f"Estimated Payoff Time: {months} months at {weighted_apr * 100:.2f}% APR")
        df = pd.DataFrame({"Month": list(range(months)), "Balance": balances})
        chart = alt.Chart(df).mark_line().encode(
            x="Month",
            y=alt.Y("Balance", title="Projected Balance ($)"),
            tooltip=["Month", "Balance"]
        ).properties(title="Credit Card Payoff Projection")
        st.altair_chart(chart, use_container_width=True)
    else:
        st.error("You're not paying down your balance. Adjust expenses or reserve %.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Net Income", f"${monthly_net_income:,.2f}")
    col2.metric("After Expenses", f"${income_after_expenses:,.2f}")
    col3.metric("Contribution", f"${credit_contribution:,.2f}")
