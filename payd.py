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
    <h1 style='margin-bottom:0; color: black;'>💳 Pay’d: Your Personalized Credit Strategy</h1>
    <p style='margin-top:0.5rem; font-size: 1.1rem; color: black;'>Smarter payoff planning. Real results. Designed for people who want to crush debt without compromising lifestyle.</p>
</div>
""", unsafe_allow_html=True)

# --- Main Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🧾 Income & Deductions", "📦 Expenses", "💳 Credit Cards", "📊 Results"])

# ----------------- TAB 1 -------------------
with tab1:
    st.header("🧾 Step 1: Income & Deductions")
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

        st.markdown("### 🐝 Monthly Deductions")
        rows = [st.columns(3), st.columns(3)]
        keys = list(deductions.keys())
        for i in range(6):
            rows[i // 3][i % 3].metric(keys[i], f"${deductions[keys[i]]:,.2f}")

    with col2:
        insurance = st.number_input("Monthly Health Insurance ($)", min_value=0, value=300, step=25, key="insurance")

        monthly_net = (salary - fed - state - ss - medicare - retire_contrib) / 12 - insurance

        st.subheader("📈 Net Income Overview")
        st.metric("Monthly Income (Before Deductions)", f"${monthly_income:,.2f}")
        st.metric("Net Monthly Income (After Deductions)", f"${monthly_net:,.2f}")
        st.markdown(f"**Total Deductions:** <span style='color: green;'>${sum(deductions.values()):,.2f}</span> / month", unsafe_allow_html=True)

    income_left = monthly_net

# ----------------- TAB 2 -------------------
with tab2:
    st.header("📦 Step 2: Monthly Expenses")
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
    income_left -= total_exp
    st.markdown(f"### 💰 Total Monthly Expenses: `${total_exp:,.2f}`")
    card_pct = st.slider("% of expenses charged to credit", 0, 100, 50) / 100
    st.metric("Updated Net After Expenses", f"${income_left:,.2f}")

# ----------------- TAB 3 -------------------
with tab3:
    st.markdown("""
    <style>
    .metric-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .metric-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #222;
    }
    .debt-value {
        font-size: 2rem;
        color: #e53935;
        font-weight: bold;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("💳 Credit Cards")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-header'>Debt</div>", unsafe_allow_html=True)

        total_debt = sum(c["balance"] for c in st.session_state.cards.values()) if "cards" in st.session_state else 0
        st.markdown(f"<div class='debt-value'>${total_debt:,.0f}</div>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>Monthly Payment</strong><br>${credit_contrib:,.0f}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Add credit card input form
        with st.form("card_form", clear_on_submit=True):
            name = st.text_input("Card Name")
            balance = st.number_input("Balance ($)", min_value=0, step=50)
            apr = st.number_input("APR (%)", min_value=0.0, step=0.1)
            if st.form_submit_button("Add Card") and name:
                st.session_state.cards[name] = {"balance": balance, "apr": apr / 100}

        # Table of cards
        if st.session_state.cards:
            df_cards = pd.DataFrame([
                {"Card": k, "Balance": f"${v['balance']:,.0f}", "APR": f"{v['apr']*100:.1f}%"}
                for k, v in st.session_state.cards.items()
            ])
            st.markdown("<div class='section-title'>Credit Cards</div>", unsafe_allow_html=True)
            st.dataframe(df_cards, use_container_width=True, height=200)

    with col2:
        # Debt Payoff Timeline chart
        if st.session_state.cards:
            chart_data = pd.DataFrame({'Month': list(range(len(b_list))), 'Balance': b_list})
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown("<div class='metric-header'>Debt Payoff Timeline</div>", unsafe_allow_html=True)
            st.altair_chart(
                alt.Chart(chart_data).mark_line().encode(
                    x="Month",
                    y="Balance",
                    tooltip=["Month", "Balance"]
                ).properties(height=150),
                use_container_width=True
            )
            st.markdown(f"<p>You could be debt-free in about <strong>{payoff_months} months</strong></p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Consolidation suggestion
        if len(st.session_state.cards) >= 2:
            highest_apr = max(st.session_state.cards.items(), key=lambda x: x[1]["apr"])
            lowest_apr = min(st.session_state.cards.items(), key=lambda x: x[1]["apr"])
            if highest_apr[1]["apr"] > lowest_apr[1]["apr"]:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown("<div class='metric-header'>Consolidation Insights</div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <p>Consider consolidating your debt?</p>
                    <p><strong>${highest_apr[1]['balance']:,.0f}</strong> from <strong>{highest_apr[0]}</strong> to <strong>{lowest_apr[0]}</strong></p>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


# ----------------- TAB 4 -------------------
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

with tab4:
    st.header("📊 Final Plan & Payoff Strategy")
    reserve = st.slider("% of leftover income to reserve", 0, 50, 20) / 100
    credit_contrib = income_left * (1 - reserve)
    reuse = total_exp * card_pct
    reduction = credit_contrib - reuse

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

    st.divider()
    with st.expander("🤖 Smart Budget Advice"):
        if st.button("Get My Tips"):
            with st.spinner("Generating insights..."):
                st.info(get_tips(monthly_net, total_exp, st.session_state.cards, credit_contrib, reserve))

    with st.expander("💬 Ask a Financial Question"):
        q = st.text_area("Your question about debt, spending, or plans:")
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
