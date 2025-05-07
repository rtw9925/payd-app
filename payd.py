import streamlit as st
import numpy as np
import pandas as pd
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
h1, h2, h3, h4 {
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.metric-box {
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 1rem;
    background-color: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# --- Sidebar Navigation ---
st.sidebar.image("https://i.imgur.com/2wG1k4t.png", width=120)
st.sidebar.title("Pay’d")
page = st.sidebar.radio("Menu", ["Overview", "Credit Cards", "Payoff Plan", "Insights"])
st.sidebar.markdown("---")
st.sidebar.button("Help")
st.sidebar.button("Log out")

# --- Income & Expense Calculation ---
if "expenses" not in st.session_state:
    st.session_state.expenses = {}

if "cards" not in st.session_state:
    st.session_state.cards = {}

salary = 60000
fed_tax = 0.12
state_tax = 0.06
retirement = 0.05
insurance = 300

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
    "SS Tax": ss / 12,
    "Medicare": medicare / 12,
    "401(k)": retire_contrib / 12,
    "Insurance": insurance
}

monthly_net = (salary - fed - state - ss - medicare - retire_contrib) / 12 - insurance
income_left = monthly_net

total_exp = sum(st.session_state.expenses.values())
income_left -= total_exp
reuse = total_exp * 0.5
credit_contrib = income_left * 0.8
reduction = credit_contrib - reuse

# --- Page Content ---
if page == "Overview":
    st.header("💼 Overview")
    st.subheader("Monthly Income & Deductions")
    col1, col2 = st.columns(2)
    col1.metric("Monthly Gross Income", f"${monthly_income:,.2f}")
    col2.metric("Net Income After Deductions", f"${monthly_net:,.2f}")
    st.markdown("#### Deductions Breakdown")
    for key, val in deductions.items():
        st.metric(label=key, value=f"${val:,.2f}")

    st.subheader("Monthly Expenses")
    if st.session_state.expenses:
        df_exp = pd.DataFrame(st.session_state.expenses.items(), columns=["Type", "Amount"])
        st.dataframe(df_exp, use_container_width=True)
    st.metric("Total Expenses", f"${total_exp:,.2f}")

elif page == "Credit Cards":
    st.header("💳 Credit Cards")

    debt = sum(c["balance"] for c in st.session_state.cards.values())
    available_credit = 15000
    payment = 750

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Current Credit Snapshot")
        st.metric("Debt", f"${debt:,.0f}")
        st.metric("Available Credit", f"${available_credit:,.0f}")
        st.metric("Monthly Payment", f"${payment:,.0f}")

    with col2:
        st.markdown("#### Debt Payoff Timeline")
        months = list(range(0, 19, 6))
        balances = [debt * (1 - 0.05 * i) for i in range(len(months))]
        df = pd.DataFrame({"Month": months, "Balance": balances})
        chart = alt.Chart(df).mark_line().encode(x="Month", y="Balance")
        st.altair_chart(chart, use_container_width=True)
        st.caption("You could be debt-free in about 18 months")

    if st.session_state.cards:
        st.markdown("#### Card Balances")
        df_cards = pd.DataFrame([
            {"Card": k, "Balance": v["balance"], "APR": f"{v['apr']*100:.1f}%"}
            for k, v in st.session_state.cards.items()
        ])
        st.dataframe(df_cards, use_container_width=True)

    with st.form("add_card", clear_on_submit=True):
        name = st.text_input("Card Name")
        balance = st.number_input("Balance ($)", min_value=0)
        apr = st.number_input("APR (%)", min_value=0.0)
        if st.form_submit_button("Add Card") and name:
            st.session_state.cards[name] = {"balance": balance, "apr": apr / 100}

elif page == "Payoff Plan":
    st.header("📊 Final Plan & Payoff Strategy")
    bal = sum(c["balance"] for c in st.session_state.cards.values())
    apr_wt = sum(c["balance"] * c["apr"] for c in st.session_state.cards.values()) / bal if bal else 0
    r_month = apr_wt / 12
    b = bal
    m = 0
    b_list = []
    while b > 0 and m < 600:
        i = b * r_month
        b += i + reuse - credit_contrib
        b_list.append(b)
        if b > bal * 10: break
        m += 1
    payoff_months = m if b <= 0 else None

    col1, col2 = st.columns(2)
    col1.metric("Monthly Reused on Cards", f"${reuse:,.2f}")
    col2.metric("Net Monthly Reduction", f"${reduction:,.2f}")

    if payoff_months:
        st.success(f"✅ Estimated Payoff Time: {payoff_months} months")
        chart_data = pd.DataFrame({'Month': list(range(m)), 'Balance': b_list})
        st.altair_chart(
            alt.Chart(chart_data).mark_line().encode(
                x="Month",
                y="Balance",
                tooltip=["Month", "Balance"]
            ).properties(height=350, title="Credit Payoff Projection"),
            use_container_width=True
        )
    else:
        st.error("❌ Your debt is growing. Reconsider your expenses or contribution.")

elif page == "Insights":
    st.header("🧠 Smart Budget Insights")

    def get_tips(income, expenses, cards, contrib, reserve):
        prompt = f"""
        I bring home ${income:.2f} monthly, spend ${expenses:.2f}, and reserve {int(reserve*100)}%.
        I pay ${contrib:.2f} toward credit card debt monthly across {len(cards)} cards.
        Give me 3 high-impact budgeting or payoff suggestions.
        """
        try:
            res = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a savvy credit advisor."},
                    {"role": "user", "content": prompt}
                ]
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"❌ API Error: {e}"

    if st.button("Get My Personalized Tips"):
        with st.spinner("Generating insights..."):
            st.info(get_tips(monthly_net, total_exp, st.session_state.cards, credit_contrib, 0.2))

    st.markdown("### 💬 Ask a Custom Question")
    q = st.text_area("Your financial question:")
    if st.button("Ask Advisor") and q.strip():
        with st.spinner("Thinking..."):
            try:
                out = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a debt coach."},
                        {"role": "user", "content": q.strip()}
                    ]
                )
                st.success(out.choices[0].message.content)
            except Exception as e:
                st.error(f"❌ GPT Error: {e}")

st.caption("Built by Ryan Worthington • © 2025 Pay’d")
