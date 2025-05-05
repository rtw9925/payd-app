import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Pay’d • Smart Credit Planning", page_icon="💳", layout="wide")

st.markdown("""
<style>
body {
    background-color: #f0f4f8;
    font-family: 'Segoe UI', sans-serif;
}
.stButton > button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.1rem;
    transition: 0.2s ease;
}
.stButton > button:hover {
    transform: scale(1.04);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.stMetric label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #555;
}
.stTabs [data-baseweb="tab"] {
    font-size: 1.05rem;
    font-weight: bold;
}
.stSlider, .stTextInput, .stNumberInput, .stDataFrame, .stForm, .stSelectbox {
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
.progress-container {
    background: #e0f2fe;
    border-radius: 10px;
    height: 24px;
    width: 100%;
    overflow: hidden;
    margin: 1rem 0;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #34d399, #10b981);
    text-align: center;
    color: white;
    font-weight: 600;
    transition: width 0.4s ease-in-out;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='padding: 2rem; border-radius: 14px; background: linear-gradient(135deg, #e3f2fd 0%, #e8f5e9 100%); border: 1px solid #d0d0d0;'>
    <h1 style='margin-bottom:0;'>🎯 Welcome to Pay’d: Gamify Your Debt Payoff</h1>
    <p style='margin-top:0.5rem; font-size: 1.05rem;'>Turn your credit payoff into a mission. Track your progress, level up your savings, and get AI tips along the way.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("## 🔄 Select a Step Below")
tab1, tab2, tab3, tab4 = st.tabs(["🧾 Income", "📦 Expenses", "💳 Credit Cards", "📊 Results"])

with tab1:
    st.header("🧾 Income & Deductions")
    salary = st.number_input("Gross Annual Salary ($)", 0, 500000, 85000, step=1000)
    fed = st.slider("Federal Tax %", 0, 37, 12) / 100
    state = st.slider("State Tax %", 0, 15, 5) / 100
    retirement = st.slider("401(k) Contribution %", 0, 20, 5) / 100
    insurance = st.number_input("Monthly Insurance ($)", 0, 2000, 300, step=25)

    contrib = salary * retirement
    taxable = salary - contrib
    ss = min(taxable, 168600) * 0.062
    medicare = taxable * 0.0145
    fed_tax = taxable * fed
    state_tax = taxable * state

    net_month = (salary - fed_tax - state_tax - ss - medicare - contrib) / 12 - insurance
    st.metric("💵 Net Income (monthly)", f"${net_month:,.2f}")

with tab2:
    st.header("📦 Monthly Expenses")
    if "expenses" not in st.session_state:
        st.session_state.expenses = {}
    with st.form("expense_form", clear_on_submit=True):
        name = st.text_input("Expense Name")
        amount = st.number_input("Amount ($)", 0, 10000, step=50)
        if st.form_submit_button("Add Expense") and name:
            st.session_state.expenses[name] = amount

    if st.session_state.expenses:
        df_exp = pd.DataFrame(st.session_state.expenses.items(), columns=["Name", "Amount"])
        st.dataframe(df_exp, use_container_width=True)
    total_exp = sum(st.session_state.expenses.values())
    card_pct = st.slider("% of expenses charged to credit", 0, 100, 50) / 100

    st.metric("📉 Total Expenses", f"${total_exp:,.2f}")

with tab3:
    st.header("💳 Credit Cards")
    if "cards" not in st.session_state:
        st.session_state.cards = {}
    with st.form("card_form", clear_on_submit=True):
        name = st.text_input("Card Name")
        bal = st.number_input("Balance ($)", 0, 100000, step=100)
        apr = st.number_input("APR (%)", 0.0, 100.0, step=0.1)
        if st.form_submit_button("Add Card") and name:
            st.session_state.cards[name] = {"balance": bal, "apr": apr / 100}

    if st.session_state.cards:
        df_cards = pd.DataFrame([
            {"Card": k, "Balance": v["balance"], "APR": f"{v['apr']*100:.1f}%"}
            for k, v in st.session_state.cards.items()
        ])
        st.dataframe(df_cards, use_container_width=True)

with tab4:
    st.header("📊 Your Results & Strategy")

    colA, colB = st.columns(2)
    colA.metric("💵 Net Income (Monthly)", f"${net_month:,.2f}")
    colB.metric("📊 Income After Expenses", f"${net_month - total_exp:,.2f}")

    income_left = net_month - total_exp
    reserve_pct = st.slider("Reserve % of leftover for savings", 0, 50, 20) / 100
    to_cards = income_left * (1 - reserve_pct)
    reuse = total_exp * card_pct
    reduction = to_cards - reuse

    balance = sum(c["balance"] for c in st.session_state.cards.values())
    apr_avg = sum(c["balance"] * c["apr"] for c in st.session_state.cards.values()) / balance if balance else 0
    monthly_rate = apr_avg / 12
    debt = balance
    months = 0
    history = []
    while debt > 0 and months < 600:
        interest = debt * monthly_rate
        debt += interest + reuse - to_cards
        history.append(debt)
        if debt > balance * 10:
            break
        months += 1

    if debt <= 0:
        st.success(f"🎉 Debt-Free in {months} months!")
        pct_done = int(100 * (1 - history[-1] / balance)) if balance else 100
        st.markdown("""
        <div class='progress-container'>
            <div class='progress-fill' style='width:{0}%'>🏁 {0}% Complete</div>
        </div>
        """.format(min(100, int(100 * (1 - history[-1] / balance)))), unsafe_allow_html=True)
        df_proj = pd.DataFrame({'Month': list(range(months)), 'Balance': history})
        st.altair_chart(alt.Chart(df_proj).mark_line().encode(
            x="Month", y="Balance", tooltip=["Month", "Balance"]
        ).properties(height=350, title="Payoff Timeline"), use_container_width=True)
    else:
        st.error("⚠️ You're not reducing your debt. Revisit your spending or contribution.")

    with st.expander("💡 Get Smart Payoff Tips"):
        if st.button("Coach Me"):
            with st.spinner("Analyzing your situation..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a smart and strategic financial advisor."},
                            {"role": "user", "content": f"My monthly net is ${net_month:.2f}, expenses are ${total_exp:.2f}, and I put ${to_cards:.2f} toward credit card debt. Suggest 3 things I can do better."}
                        ]
                    )
                    st.info(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error: {e}")

    st.caption("🚀 Built with 💙 by Ryan Worthington • 2025")
