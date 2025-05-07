import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.set_page_config(page_title="Pay’d • Smart Credit Planning", page_icon="💳", layout="wide")

# --- Global CSS Styling ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background-color: #111;
    color: #f5f5f5;
}

h1, h2, h3, h4 {
    font-weight: 700;
    color: #fff;
}

.metric-card {
    background-color: #1c1c1e;
    border: 1px solid #2c2c2e;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
}

.metric-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #d0d0d0;
}

.debt-value {
    font-size: 2.2rem;
    color: #ff4b4b;
    font-weight: bold;
}

.section-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #eee;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

input, textarea {
    background-color: #2c2c2e !important;
    color: #fff !important;
    border-radius: 8px !important;
    border: 1px solid #444 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🧾 Income & Deductions", "📦 Expenses", "💳 Credit Cards", "📊 Results"])

# ----------------- TAB 1 -------------------
with tab1:
    st.header("🧾 Income & Deductions")
    col1, col2 = st.columns([2, 1])

    with col1:
        salary = st.number_input("Annual Gross Salary ($)", min_value=0, value=60000, step=1000)
        fed_tax = st.slider("Federal Tax Rate", 0, 37, 12) / 100
        state_tax = st.slider("State Tax Rate", 0, 15, 6) / 100
        retirement = st.slider("401(k) Contribution %", 0, 20, 5) / 100

        monthly_income = salary / 12
        retire_contrib = salary * retirement
        taxable = salary - retire_contrib
        ss = min(taxable, 168600) * 0.062
        medicare = taxable * 0.0145
        fed = taxable * fed_tax
        state = taxable * state_tax
        insurance = st.session_state.get("insurance", 300)

        deductions = {
            "Federal Tax": fed / 12,
            "State Tax": state / 12,
            "SS Tax": ss / 12,
            "Medicare": medicare / 12,
            "401(k)": retire_contrib / 12,
            "Insurance": insurance
        }

        for label, value in deductions.items():
            st.markdown(f"<div class='metric-card'><div class='metric-header'>{label}</div><div>${value:,.2f}</div></div>", unsafe_allow_html=True)

    with col2:
        insurance = st.number_input("Monthly Health Insurance ($)", min_value=0, value=300, step=25, key="insurance")
        monthly_net = (salary - fed - state - ss - medicare - retire_contrib) / 12 - insurance
        income_left = monthly_net

        st.markdown(f"<div class='metric-card'><div class='metric-header'>Monthly Income (Before Deductions)</div><div>${monthly_income:,.2f}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><div class='metric-header'>Net Monthly Income</div><div>${monthly_net:,.2f}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><div class='metric-header'>Total Monthly Deductions</div><div>${sum(deductions.values()):,.2f}</div></div>", unsafe_allow_html=True)

# ----------------- TAB 2 -------------------
with tab2:
    st.header("📦 Monthly Expenses")
    if "expenses" not in st.session_state:
        st.session_state.expenses = {}

    with st.form("add_expense", clear_on_submit=True):
        e_name = st.text_input("Expense Type")
        e_amount = st.number_input("Amount ($)", min_value=0, step=25)
        if st.form_submit_button("Add Expense") and e_name:
            st.session_state.expenses[e_name] = e_amount

    if st.session_state.expenses:
        df_exp = pd.DataFrame(st.session_state.expenses.items(), columns=["Type", "Amount"])
        st.dataframe(df_exp, use_container_width=True)

    total_exp = sum(st.session_state.expenses.values())
    card_pct = st.slider("% of expenses charged to credit", 0, 100, 50) / 100
    income_left -= total_exp

    st.markdown(f"<div class='metric-card'><div class='metric-header'>Total Monthly Expenses</div><div>${total_exp:,.2f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card'><div class='metric-header'>Updated Net After Expenses</div><div>${income_left:,.2f}</div></div>", unsafe_allow_html=True)

# ----------------- TAB 3 -------------------
with tab3:
    st.header("💳 Credit Cards")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<div class='metric-card'><div class='metric-header'>Debt</div>", unsafe_allow_html=True)
        total_debt = sum(c["balance"] for c in st.session_state.get("cards", {}).values())
        st.markdown(f"<div class='debt-value'>${total_debt:,.0f}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.form("card_form", clear_on_submit=True):
            name = st.text_input("Card Name")
            balance = st.number_input("Balance ($)", min_value=0, step=50)
            apr = st.number_input("APR (%)", min_value=0.0, step=0.1)
            if st.form_submit_button("Add Card") and name:
                if "cards" not in st.session_state:
                    st.session_state.cards = {}
                st.session_state.cards[name] = {"balance": balance, "apr": apr / 100}

        if st.session_state.get("cards"):
            df_cards = pd.DataFrame([
                {"Card": k, "Balance": f"${v['balance']:,.0f}", "APR": f"{v['apr']*100:.1f}%"}
                for k, v in st.session_state.cards.items()
            ])
            st.markdown("<div class='section-title'>Credit Cards</div>", unsafe_allow_html=True)
            st.dataframe(df_cards, use_container_width=True, height=200)

    with col2:
        if st.session_state.get("cards"):
            bal = sum(c["balance"] for c in st.session_state.cards.values())
            apr_wt = sum(c["balance"] * c["apr"] for c in st.session_state.cards.values()) / bal if bal else 0
            r_month = apr_wt / 12
            b = bal
            m = 0
            b_list = []
            reuse = total_exp * card_pct
            credit_contrib = income_left * 0.8
            while b > 0 and m < 600:
                i = b * r_month
                b += i + reuse - credit_contrib
                b_list.append(b)
                if b > bal * 10: break
                m += 1
            payoff_months = m if b <= 0 else None

            st.markdown("<div class='metric-card'><div class='metric-header'>Debt Payoff Timeline</div>", unsafe_allow_html=True)
            if payoff_months:
                chart_data = pd.DataFrame({'Month': list(range(m)), 'Balance': b_list})
                st.altair_chart(
                    alt.Chart(chart_data).mark_line().encode(
                        x="Month",
                        y="Balance",
                        tooltip=["Month", "Balance"]
                    ).properties(height=200),
                    use_container_width=True
                )
                st.markdown(f"<p>You could be debt-free in about <strong>{payoff_months} months</strong></p>", unsafe_allow_html=True)
            else:
                st.markdown("Debt is increasing — reconsider your budget.")
            st.markdown("</div>", unsafe_allow_html=True)

            if len(st.session_state.cards) >= 2:
                highest_apr = max(st.session_state.cards.items(), key=lambda x: x[1]["apr"])
                lowest_apr = min(st.session_state.cards.items(), key=lambda x: x[1]["apr"])
                if highest_apr[1]["apr"] > lowest_apr[1]["apr"]:
                    st.markdown("<div class='metric-card'><div class='metric-header'>Consolidation Insights</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <p>Consider consolidating your debt?</p>
                        <p><strong>${highest_apr[1]['balance']:,.0f}</strong> from <strong>{highest_apr[0]}</strong> to <strong>{lowest_apr[0]}</strong></p>
                    """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- TAB 4 -------------------
with tab4:
    st.header("📊 Final Plan & Smart Suggestions")
    reserve = st.slider("% of leftover income to reserve", 0, 50, 20) / 100
    credit_contrib = income_left * (1 - reserve)
    reuse = total_exp * card_pct
    reduction = credit_contrib - reuse

    col1, col2 = st.columns(2)
    col1.markdown(f"<div class='metric-card'><div class='metric-header'>Monthly Reused on Cards</div><div>${reuse:,.2f}</div></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'><div class='metric-header'>Net Monthly Reduction</div><div>${reduction:,.2f}</div></div>", unsafe_allow_html=True)

    st.subheader("🤖 Get Tailored Advice")
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

    if st.button("Get Smart Tips"):
        with st.spinner("Generating insights..."):
            st.info(get_tips(monthly_net, total_exp, st.session_state.get("cards", {}), credit_contrib, reserve))

st.caption("Built by Ryan Worthington • © 2025 Pay’d")
