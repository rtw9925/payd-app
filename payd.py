import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Pay’d • Smart Credit Planning", page_icon="💳", layout="wide")

st.markdown("""
<style>
div[data-testid="stForm"], .stButton > button, .stNumberInput, .stTextInput, .stSlider, .stTabs, .stMetric, .stDataFrame {
    border-radius: 12px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.stMetric label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #555;
}
h1, h2, h3, h4 {
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='padding: 2rem; border-radius: 14px; background: linear-gradient(135deg, #e3f2fd 0%, #e8f5e9 100%); border: 1px solid #d0d0d0;'>
    <h1 style='margin-bottom:0;'>💳 Pay’d: Your Personalized Credit Strategy</h1>
    <p style='margin-top:0.5rem; font-size: 1.1rem;'>Smarter payoff planning. Real results. Designed for people who want to crush debt without compromising lifestyle.</p>
</div>
""", unsafe_allow_html=True)

# --- Main Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🧾 Income & Deductions", "📦 Expenses", "💳 Credit Cards", "📊 Results"])

with tab1:
    st.header("🧾 Step 1: Income & Deductions")
    col1, col2 = st.columns([2, 1])

    with col1:
        salary = st.number_input("Annual Gross Salary ($)", min_value=0, value=60000, step=1000)
        fed_tax = st.slider("Federal Tax Rate", 0, 37, 12) / 100
        state_tax = st.slider("State Tax Rate", 0, 15, 6) / 100
        retirement = st.slider("401(k) Contribution %", 0, 20, 5) / 100

    with col2:
        insurance = st.number_input("Monthly Health Insurance ($)", min_value=0, value=300, step=25)

        monthly_income = salary / 12
        retire_contrib = salary * retirement
        taxable = salary - retire_contrib
        ss = min(taxable, 168600) * 0.062
        medicare = taxable * 0.0145
        fed = taxable * fed_tax
        state = taxable * state_tax
        monthly_net = (salary - fed - state - ss - medicare - retire_contrib) / 12 - insurance

        deductions = {
            "Federal Tax": fed / 12,
            "State Tax": state / 12,
            "SS Tax": ss / 12,
            "Medicare": medicare / 12,
            "401(k)": retire_contrib / 12,
            "Insurance": insurance
        }

        st.subheader("📈 Net Income Overview")
        st.metric("Monthly Income (Before Deductions)", f"${monthly_income:,.2f}")
        st.metric("Net Monthly Income (After Deductions)", f"${monthly_net:,.2f}")

    income_left = monthly_net

    st.markdown("### 🐝 Monthly Deductions")
    with st.container():
        dcol1, _, dcol2 = st.columns([1.2, 0.1, 1.2])
        items = list(deductions.items())
        for i, (label, val) in enumerate(items):
            (dcol1 if i < 3 else dcol2).metric(label, f"${val:,.2f}")
        st.markdown(f"**Total Deductions:** <span style='color: green;'>${sum(deductions.values()):,.2f}</span> / month", unsafe_allow_html=True)

# (Tab 2–4 remain unchanged)
# ...
