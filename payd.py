import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Pay’d • Smart Credit Planning", page_icon="💳", layout="wide")

# --- Custom CSS Styling for exact match ---
st.markdown("""
<style>
body {
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #fafafa;
}
.sidebar .sidebar-content {
    padding: 1rem;
}
/* Sidebar Highlight */
.css-1v3fvcr, .css-1d391kg, .css-1v0mbdj {
    background-color: #e0f2fe !important;
    border-left: 4px solid #3b82f6 !important;
}
/* Card Styling */
.card {
    border-radius: 12px;
    padding: 1.25rem;
    background: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    text-align: center;
}
.gradient-header {
    background: linear-gradient(135deg, #e3f2fd 0%, #e8f5e9 100%);
    padding: 1.5rem;
    border-radius: 14px;
    border: 1px solid #d0d0d0;
    margin-bottom: 2rem;
}
.red-bar {
    background: #ef5350;
    height: 6px;
    width: 100%;
    border-radius: 4px;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- Top Banner ---
st.markdown("""
<div class='gradient-header'>
    <h2 style='margin-bottom:0;'>Credit Cards</h2>
    <p style='margin-top:0.5rem; font-size: 1.1rem;'>Track your credit usage and plan your payoff effectively.</p>
</div>
""", unsafe_allow_html=True)

# --- Card Overview Section ---
st.markdown("""
<div style='display: flex; gap: 1.5rem;'>
  <div class='card' style='flex:1;'>
    <h3 style='color:#d32f2f;'>$10,250</h3>
    <p>Debt</p>
    <div class='red-bar'></div>
  </div>
  <div class='card' style='flex:1;'>
    <h3 style='color:#1565c0;'>$15,000</h3>
    <p>Available Credit</p>
  </div>
  <div class='card' style='flex:1;'>
    <h3 style='color:#2e7d32;'>$750</h3>
    <p>Monthly Payment</p>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Debt Payoff Timeline ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 📉 Debt Payoff Timeline")
months = list(range(0, 19, 6))
balances = [10250 * (1 - 0.05 * i) for i in range(len(months))]
df = pd.DataFrame({"Month": months, "Balance": balances})
st.altair_chart(alt.Chart(df).mark_line().encode(x="Month", y="Balance"), use_container_width=True)
st.caption("You could be debt-free in about 18 months")

# --- Card Balances Table ---
st.markdown("#### 💳 Card Balances")
data = {
    "Card": ["Chase Freedom", "Citi Double Cash", "Discover it"],
    "Balance": [5200, 3500, 1550],
    "APR": ["18.9%", "21.7%", "17.4%"]
}
st.dataframe(pd.DataFrame(data), use_container_width=True)

# --- Consolidation Insight Block ---
st.markdown("""
<div class='card' style='margin-top:2rem;'>
    <h4>Consolidation Insights</h4>
    <p>Consider consolidating your debt?</p>
    <p><strong>$3,500</strong> from Citi Double Cash to Discover it</p>
</div>
""", unsafe_allow_html=True)

st.caption("Built by Ryan Worthington • © 2025 Pay’d")
