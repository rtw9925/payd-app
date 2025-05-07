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
.sidebar .sidebar-content { padding: 1rem; }
.metric-box { border-radius: 12px; padding: 1.25rem; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.05); text-align: center; }
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

# --- Tabs Layout ---
tab1, tab2, tab3, tab4 = st.tabs(["🧾 Income & Deductions", "📦 Expenses", "💳 Credit Cards", "📊 Results"])

# Shared state init
if "expenses" not in st.session_state:
    st.session_state.expenses = {}
if "cards" not in st.session_state:
    st.session_state.cards = {}

# ----------------- TAB 1 -------------------
with tab1:
    st.markdown("<div class='gradient-header'><h2>Income & Deductions</h2><p>Understand what you truly take home each month.</p></div>", unsafe_allow_html=True)

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

        st.subheader("Monthly Deductions")
        for k, v in deductions.items():
            st.metric(k, f"${v:,.2f}")

    with col2:
        insurance = st.number_input("Monthly Health Insurance ($)", min_value=0, value=300, step=25, key="insurance")
        monthly_net = (salary - fed - state - ss - medicare - retire_contrib) / 12 - insurance
        st.metric("Monthly Income (Before Deductions)", f"${monthly_income:,.2f}")
        st.metric("Net Monthly Income (After Deductions)", f"${monthly_net:,.2f}")
        st.markdown(f"**Total Deductions:** <span style='color: green;'>${sum(deductions.values()):,.2f}</span> / month", unsafe_allow_html=True)

    income_left = monthly_net

# ----------------- TAB 2 -------------------
with tab2:
    st.markdown("<div class='gradient-header'><h2>Monthly Expenses</h2><p>Track your core living expenses and budget behavior.</p></div>", unsafe_allow_html=True)

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
    st.metric("Total Monthly Expenses", f"${total_exp:,.2f}")
    income_left -= total_exp
    st.metric("Net After Expenses", f"${income_left:,.2f}")

# ----------------- TAB 3 -------------------
with tab3:
    st.markdown("<div class='gradient-header'><h2>Credit Cards</h2><p>Track your credit usage and plan your payoff effectively.</p></div>", unsafe_allow_html=True)

    debt = sum(c["balance"] for c in st.session_state.cards.values())
    available_credit = 15000
    payment = 750

    st.markdown("""
    <div style='display: flex; gap: 1.5rem;'>
      <div class='metric-box' style='flex:1;'>
        <h3 style='color:#d32f2f;'>${:,.0f}</h3>
        <p>Debt</p>
        <div class='red-bar'></div>
      </div>
      <div class='metric-box' style='flex:1;'>
        <h3 style='color:#1565c0;'>${:,.0f}</h3>
        <p>Available Credit</p>
      </div>
      <div class='metric-box' style='flex:1;'>
        <h3 style='color:#2e7d32;'>${:,.0f}</h3>
        <p>Monthly Payment</p>
      </div>
    </div>
    """.format(debt, available_credit, payment), unsafe_allow_html=True)

    st.markdown("#### 📉 Debt Payoff Timeline")
    months = list(range(0, 19, 6))
    balances = [debt * (1 - 0.05 * i) for i in range(len(months))]
    df = pd.DataFrame({"Month": months, "Balance": balances})
    st.altair_chart(alt.Chart(df).mark_line().encode(x="Month", y="Balance"), use_container_width=True)
    st.caption("You could be debt-free in about 18 months")

    if st.session_state.cards:
        st.markdown("#### 💳 Card Balances")
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

# ----------------- TAB 4 -------------------
with tab4:
    st.markdown("<div class='gradient-header'><h2>Final Strategy</h2><p>View your projected outcomes and receive smart advice.</p></div>", unsafe_allow_html=True)

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
                        {"role": "system", "content": "You are a professioanl and creative credit advisor."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return res.choices[0].message.content
            except Exception as e:
                return f"❌ API Error: {e}"

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
                            {"role": "system", "content": "You are a professioanl and creative debt coach."},
                            {"role": "user", "content": q.strip()}
                        ]
                    )
                    st.success(out.choices[0].message.content)
                except Exception as e:
                    st.error(f"❌ GPT Error: {e}")

st.caption("Built by Ryan Worthington • © 2025 Pay’d")
