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

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Step 1: Income & Deductions",
    "Step 2: Expenses",
    "Step 3: Credit Cards",
    "\ud83d\udcca Results"
])

# ----------------- TAB 1 -------------------
with tab1:
    st.subheader("\ud83d\udc64 Income & Deductions")
    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            salary = st.number_input("Annual Gross Salary ($)", min_value=0, value=45000, step=1000)
            state_tax_rate = st.slider("State Tax Rate", 0, 15, 6, step=1, format="%d%%") / 100
            fed_tax_rate = st.slider("Federal Tax Rate", 0, 37, 12, step=1, format="%d%%") / 100
            retirement_pct = st.slider("401(k) Contribution", 0, 20, 5, step=1, format="%d%%") / 100

        with col2:
            health_insurance = st.number_input("Health Insurance Deduction ($)", min_value=0, value=300, step=25)
            retirement_contribution = salary * retirement_pct
            taxable_salary = salary - retirement_contribution
            ss_tax = min(taxable_salary, 168600) * 0.062
            medicare_tax = taxable_salary * 0.0145
            federal_tax = taxable_salary * fed_tax_rate
            state_tax = taxable_salary * state_tax_rate

            monthly_net_income = (salary - federal_tax - state_tax - ss_tax - medicare_tax - retirement_contribution) / 12 - health_insurance
            income_after_expenses = monthly_net_income

            monthly_deductions = {
                "Federal Tax": federal_tax / 12,
                "State Tax": state_tax / 12,
                "Social Security": ss_tax / 12,
                "Medicare": medicare_tax / 12,
                "401(k)": retirement_contribution / 12,
                "Health Insurance": health_insurance
            }

            with st.container():
                st.markdown("#### \ud83d\udccc Monthly Deductions Summary")
                deduction_html = "".join([f"<strong>{k}:</strong> ${v:,.2f}<br>" for k, v in monthly_deductions.items()])
                st.markdown(f"""
                <div style="background-color: #f9f9f9; border-radius: 10px; padding: 1rem; border: 1px solid #ddd;">
                    {deduction_html}
                    <hr style="margin: 0.5rem 0;">
                    <h4 style="color: #d32f2f; margin: 0;">${sum(monthly_deductions.values()):,.2f} / mo</h4>
                </div>
                """, unsafe_allow_html=True)

# ----------------- TAB 2 -------------------
with tab2:
    st.subheader("\ud83d\udce6 Monthly Expenses")
    if "expenses" not in st.session_state:
        st.session_state.expenses = {}

    with st.form("expense_form", clear_on_submit=True):
        exp_name = st.text_input("Expense Name (e.g., Rent, Groceries)")
        exp_amt = st.number_input("Amount ($)", min_value=0, step=50)
        submitted = st.form_submit_button("➕ Add Expense")
        if submitted and exp_name:
            st.session_state.expenses[exp_name] = exp_amt

    st.markdown("#### \ud83d\udcc3 Expense Summary")
    if st.session_state.expenses:
        exp_df = pd.DataFrame(st.session_state.expenses.items(), columns=["Expense", "Amount"])
        st.dataframe(exp_df, use_container_width=True)

    total_expenses = sum(st.session_state.expenses.values())
    st.markdown(f"**Total Monthly Expenses:** `${total_expenses:,.2f}`")
    credit_spend_pct = st.slider("What % of expenses go on credit cards?", 0, 100, 50, step=5, format="%d%%") / 100
    income_after_expenses -= total_expenses

# ----------------- TAB 3 -------------------
with tab3:
    st.subheader("\ud83d\udcb3 Credit Cards")
    if "cards" not in st.session_state:
        st.session_state.cards = {}

    with st.form("card_form", clear_on_submit=True):
        card_name = st.text_input("Card Name")
        card_bal = st.number_input("Card Balance ($)", min_value=0, step=50)
        card_apr = st.number_input("Card APR (%)", min_value=0.0, step=0.1)
        if st.form_submit_button("➕ Add Card") and card_name:
            st.session_state.cards[card_name] = {"balance": card_bal, "apr": card_apr / 100}

    st.markdown("#### \ud83d\udcbc Your Credit Cards")
    if st.session_state.cards:
        card_df = pd.DataFrame([
            {"Card": name, "Balance": c["balance"], "APR": f"{c['apr'] * 100:.2f}%"}
            for name, c in st.session_state.cards.items()
        ])
        st.dataframe(card_df, use_container_width=True)

# ----------------- TAB 4 -------------------
def get_budget_advice(income, expenses, cards, contribution, reserve_pct):
    prompt = f"""
    I make ${income:.2f} after taxes and spend ${expenses:.2f} per month.
    I have {len(cards)} credit cards with a total balance of ${sum(c['balance'] for c in cards.values()):,.2f}.
    I reserve {int(reserve_pct*100)}% and contribute ${contribution:.2f} monthly to debt.

    Give me 3 personalized budgeting or credit payoff tips in plain language.
    Focus on helping me pay off debt faster while keeping some emergency savings.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a strategic, practical financial coach. Help with payoff acceleration, balance transfers, and consolidation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error from OpenAI API: {str(e)}"

with tab4:
    st.subheader("\ud83d\udcca Results & Strategy")
    reserve_pct = st.slider("How much of your leftover income would you like to reserve?", 0, 50, 20, step=5, format="%d%%") / 100

    credit_contribution = income_after_expenses * (1 - reserve_pct)
    monthly_credit_reuse = total_expenses * credit_spend_pct
    net_reduction = credit_contribution - monthly_credit_reuse

    total_balance = sum(c["balance"] for c in st.session_state.cards.values())
    weighted_apr = sum(c["balance"] * c["apr"] for c in st.session_state.cards.values()) / total_balance if total_balance else 0
    monthly_rate = weighted_apr / 12

    balance = total_balance
    months = 0
    max_months = 600
    balances = []
    while balance > 0 and months < max_months:
        interest = balance * monthly_rate
        balance += interest + monthly_credit_reuse - credit_contribution
        balances.append(balance)
        if balance > total_balance * 10:
            break
        months += 1
    months_to_payoff = months if balance <= 0 else None

    st.markdown("#### \ud83d\udcca Monthly Credit Behavior")
    col1, col2 = st.columns(2)
    col1.metric("Reused on Credit", f"${monthly_credit_reuse:,.2f}")
    col2.metric("Net Reduction", f"${net_reduction:,.2f}")

    if months_to_payoff:
        st.success(f"✅ Estimated Payoff Time: **{months_to_payoff} months** at {weighted_apr * 100:.2f}% APR")
        df = pd.DataFrame({'Month': list(range(months)), 'Balance': balances})
        chart = alt.Chart(df).mark_line().encode(
            x="Month",
            y=alt.Y("Balance", title="Projected Balance ($)"),
            tooltip=["Month", "Balance"]
        ).properties(title="Projected Credit Card Payoff Timeline")
        st.altair_chart(chart, use_container_width=True)
    else:
        st.error("❌ You're not paying down your balance. Adjust your expenses or reserve %.")

    st.markdown("#### \ud83d\udcc8 Final Financial Snapshot")
    col1, col2, col3 = st.columns(3)
    col1.metric("Net Income", f"${monthly_net_income:,.2f}")
    col2.metric("After Expenses", f"${income_after_expenses:,.2f}")
    col3.metric("Contribution", f"${credit_contribution:,.2f}")

    st.divider()

    with st.expander("\ud83e\uddd1\u200d\ud83c\udf93 AI Budget Coaching"):
        if st.button("Coach Me"):
            with st.spinner("Generating advice..."):
                tips = get_budget_advice(
                    income=monthly_net_income,
                    expenses=total_expenses,
                    cards=st.session_state.cards,
                    contribution=credit_contribution,
                    reserve_pct=reserve_pct
                )
                st.info(tips)

    with st.expander("\ud83d\udcac Ask a Custom Question"):
        user_question = st.text_area("What do you want to ask about your finances, debt, or plan?")
        if st.button("Ask GPT"):
            if user_question.strip():
                with st.spinner("Thinking..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a strategic and practical financial advisor who specializes in debt, credit cards, home lending, and budgeting."},
                                {"role": "user", "content": user_question}
                            ],
                            temperature=0.6
                        )
                        answer = response.choices[0].message.content
                        st.success(answer)
                    except Exception as e:
                        st.error(f"❌ GPT Error: {e}")

st.caption("Built with ❤️ by Ryan Worthington • © 2025 Pay’d")
