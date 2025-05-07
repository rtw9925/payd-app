import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Pay’d • Smart Credit Planning", page_icon="💳", layout="wide")

# --- Custom CSS Styling ---
st.markdown("""
<style>
body { font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] {
    background-color: #f9fafb;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    padding: 0.75rem 1rem;
}
.metric-box {
    border-radius: 12px;
    padding: 1.25rem;
    background: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    text-align: left;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.red-bar {
    background: #ef5350;
    height: 6px;
    width: 100%;
    border-radius: 4px;
    margin-top: 6px;
}
.credit-section {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
}
.section-card {
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
    background-color: #ffffff;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.card-title {
    font-weight: bold;
    margin-bottom: 0.5rem;
    font-size: 1rem;
}
.card-sub {
    color: #444;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}
.credit-table {
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["Income & Deductions", "Expenses", "Credit Cards", "Results"])

# Init state
if "cards" not in st.session_state:
    st.session_state.cards = {}
if "expenses" not in st.session_state:
    st.session_state.expenses = {}

# ---------------- Tab 1: Income ----------------
with tab1:
    st.header("Income & Deductions")
    salary = st.number_input("Annual Gross Salary ($)", min_value=0, value=60000, step=1000)
    fed_tax = st.slider("Federal Tax Rate", 0, 37, 12) / 100
    state_tax = st.slider("State Tax Rate", 0, 15, 6) / 100
    retirement = st.slider("401(k) Contribution %", 0, 20, 5) / 100
    insurance = st.number_input("Monthly Insurance ($)", min_value=0, value=300, step=25)

    monthly_income = salary / 12
    retire_contrib = salary * retirement
    taxable = salary - retire_contrib
    ss = min(taxable, 168600) * 0.062
    medicare = taxable * 0.0145
    fed = taxable * fed_tax
    state = taxable * state_tax
    deductions = {
        "Federal Tax": fed / 12,
        "State Tax": state / 12,
        "SS": ss / 12,
        "Medicare": medicare / 12,
        "401k": retire_contrib / 12,
        "Insurance": insurance
    }

    st.subheader("Monthly Summary")
    st.metric("Gross Monthly Income", f"${monthly_income:,.2f}")
    st.metric("Net Monthly Income", f"${(monthly_income - sum(deductions.values())):,.2f}")

# ---------------- Tab 2: Expenses ----------------
with tab2:
    st.header("Expenses")
    with st.form("add_expense", clear_on_submit=True):
        e_name = st.text_input("Expense Name")
        e_amount = st.number_input("Amount ($)", min_value=0)
        if st.form_submit_button("Add Expense") and e_name:
            st.session_state.expenses[e_name] = e_amount
    if st.session_state.expenses:
        df_exp = pd.DataFrame(st.session_state.expenses.items(), columns=["Type", "Amount"])
        st.dataframe(df_exp, use_container_width=True)

# ---------------- Tab 3: Credit Cards ----------------
with tab3:
    st.markdown("<h2>Credit Cards</h2>", unsafe_allow_html=True)

    debt = sum(c["balance"] for c in st.session_state.cards.values())
    payment = 750

    st.markdown(f"""
    <div class='credit-section'>
        <div class='metric-box' style='flex: 1;'>
            <div>
                <div style='font-size: 1.25rem; font-weight: bold; color: #d32f2f;'>${debt:,.0f}</div>
                <div style='font-size: 0.95rem;'>Debt</div>
                <div class='red-bar'></div>
            </div>
        </div>
        <div class='metric-box' style='flex: 1;'>
            <div>
                <div style='font-size: 1.25rem; font-weight: bold; color: #1565c0;'>${payment:,.0f}</div>
                <div style='font-size: 0.95rem;'>Monthly Payment</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Payoff Timeline
    st.markdown("<div class='section-card'><div class='card-title'>Debt Payoff Timeline</div>", unsafe_allow_html=True)
    months = list(range(0, 19, 6))
    balances = [debt * (1 - 0.05 * i) for i in range(len(months))]
    df = pd.DataFrame({"Month": months, "Balance": balances})
    st.altair_chart(alt.Chart(df).mark_line().encode(x="Month", y="Balance"), use_container_width=True)
    st.caption("You could be debt-free in about 18 months")
    st.markdown("</div>", unsafe_allow_html=True)

    # Card Table
    if st.session_state.cards:
        st.markdown("<div class='section-card'><div class='card-title'>Card Balances</div>", unsafe_allow_html=True)
        df_cards = pd.DataFrame([
            {"Card": k, "Balance": v["balance"], "APR": f"{v['apr']*100:.1f}%"}
            for k, v in st.session_state.cards.items()
        ])
        st.dataframe(df_cards, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Consolidation Tip
    if "Citi Double Cash" in st.session_state.cards and "Discover it" in st.session_state.cards:
        st.markdown("""
        <div class='section-card'>
            <div class='card-title'>Consolidation Insights</div>
            <div class='card-sub'>Consider consolidating your debt?</div>
            <div>$3,500 from Citi Double Cash to Discover it</div>
        </div>
        """, unsafe_allow_html=True)

    # Add Card Form
    st.markdown("<br><h4>Add New Card</h4>", unsafe_allow_html=True)
    with st.form("add_card", clear_on_submit=True):
        name = st.text_input("Card Name")
        balance = st.number_input("Balance ($)", min_value=0)
        apr = st.number_input("APR (%)", min_value=0.0)
        if st.form_submit_button("Add Card") and name:
            st.session_state.cards[name] = {"balance": balance, "apr": apr / 100}

# ---------------- Tab 4: Results ----------------
with tab4:
    st.header("Results")
    st.write("This tab will summarize your payoff strategy and recommendations.")
