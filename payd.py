import streamlit as st
import numpy as np
import pandas as pd
from openai import OpenAI

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- Intro Banner ---
st.markdown("""
<div style='padding: 1.5rem; border-radius: 10px; background: linear-gradient(90deg, #e0f7fa, #f1f8e9); border: 1px solid #ddd;'>
    <h2 style='margin-bottom:0;'>💳 Welcome to Pay’d</h2>
    <p style='margin-top:0; font-size: 1.05rem;'>Plan your credit payoff journey based on real income, taxes, and behavior. This is not just a calculator — it’s your personalized path to debt freedom.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "Step 1: Income & Deductions",
    "Step 2: Expenses",
    "Step 3: Credit Cards",
    "📊 Results"
])

# ----------------- TAB 1 -------------------
with tab1:
    col_left, col_right = st.columns([2, 1])
    with col_left:
        salary = st.number_input("Annual Gross Salary ($)", min_value=0, value=45000, step=1000)

        state_tax_display = st.slider("State Tax Rate", 0, 15, 6, step=1, format="%d%%")
        state_tax_rate = state_tax_display / 100

        fed_tax_display = st.slider("Federal Tax Rate", 0, 37, 12, step=1, format="%d%%")
        fed_tax_rate = fed_tax_display / 100

        retirement_display = st.slider("401(k) Contribution", 0, 20, 5, step=1, format="%d%%")
        retirement_pct = retirement_display / 100

    with col_right:
        health_insurance = st.number_input("Health Insurance Deduction ($)", min_value=0, value=300, step=25)

        retirement_contribution = salary * retirement_pct
        taxable_salary = salary - retirement_contribution

        # Individual tax calculations
        ss_tax = min(taxable_salary, 168600) * 0.062
        medicare_tax = taxable_salary * 0.0145
        federal_tax = taxable_salary * fed_tax_rate
        state_tax = taxable_salary * state_tax_rate

        monthly_retirement = retirement_contribution / 12
        monthly_ss_tax = ss_tax / 12
        monthly_medicare = medicare_tax / 12
        monthly_fed = federal_tax / 12
        monthly_state = state_tax / 12
        monthly_tax = monthly_ss_tax + monthly_medicare + monthly_fed + monthly_state
        total_monthly_deductions = monthly_tax + monthly_retirement + health_insurance

        st.markdown("#### 📌 Total Monthly Deductions")
        st.markdown(f"""
        <div style="background-color: #ffffff; border-radius: 10px; padding: 1rem; border: 1px solid #ddd; font-size: 0.95rem;">
            <strong>Federal Tax:</strong> ${monthly_fed:,.2f}<br>
            <strong>State Tax:</strong> ${monthly_state:,.2f}<br>
            <strong>Social Security:</strong> ${monthly_ss_tax:,.2f}<br>
            <strong>Medicare:</strong> ${monthly_medicare:,.2f}<br>
            <strong>401(k):</strong> ${monthly_retirement:,.2f}<br>
            <strong>Health Insurance:</strong> ${health_insurance:,.2f}<br>
            <hr style="margin: 0.5rem 0;">
            <h4 style="color: #d32f2f; margin: 0;">${total_monthly_deductions:,.2f} / mo</h4>
        </div>
        """, unsafe_allow_html=True)

    monthly_net_income = (salary - federal_tax - state_tax - ss_tax - medicare_tax - retirement_contribution) / 12 - health_insurance
    income_after_expenses = monthly_net_income

# ----------------- TAB 2 -------------------
with tab2:
    st.markdown("### Add Monthly Expenses")
    if "expenses" not in st.session_state:
        st.session_state.expenses = {}
    with st.form("expense_form", clear_on_submit=True):
        exp_name = st.text_input("Expense Name (e.g., Rent, Groceries)")
        exp_amt = st.number_input("Amount ($)", min_value=0, step=50)
        if st.form_submit_button("➕ Add Expense") and exp_name:
            st.session_state.expenses[exp_name] = exp_amt
    total_expenses = sum(st.session_state.expenses.values())
    for k, v in st.session_state.expenses.items():
        st.write(f"• {k}: ${v:,.2f}")
    st.markdown(f"**Total Monthly Expenses:** `${total_expenses:,.2f}`")

    credit_spend_pct_display = st.slider("What % of expenses go on credit cards?", 0, 100, 50, step=5, format="%d%%")
    credit_spend_pct = credit_spend_pct_display / 100
    income_after_expenses -= total_expenses

# ----------------- TAB 3 -------------------
with tab3:
    st.markdown("### Add Credit Cards")
    if "cards" not in st.session_state:
        st.session_state.cards = {}
    with st.form("card_form", clear_on_submit=True):
        card_name = st.text_input("Card Name")
        card_bal = st.number_input("Card Balance ($)", min_value=0, step=50, key="bal")
        card_apr = st.number_input("Card APR (%)", min_value=0.0, step=0.1, key="apr")
        if st.form_submit_button("➕ Add Card") and card_name:
            st.session_state.cards[card_name] = {"balance": card_bal, "apr": card_apr / 100}
    for name, c in st.session_state.cards.items():
        st.write(f"• {name}: ${c['balance']:,.2f} at {c['apr']*100:.2f}% APR")

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
                {"role": "system", "content": "You are a strategic, creative, and practical financial coach. Provide personalized debt payoff tips based not just on budgeting, but also using advanced strategies like balance transfers, 0% APR offers, debt consolidation, or payment negotiation. Always explain the *why* behind each tip. Avoid repeating generic advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error from OpenAI API: {str(e)}"

with tab4:
    st.markdown("### Adjust Final Contributions")
    reserve_display = st.slider("How much of your leftover income would you like to reserve?", 0, 50, 20, step=5, format="%d%%")
    reserve_pct = reserve_display / 100

    credit_contribution = income_after_expenses * (1 - reserve_pct)
    monthly_credit_reuse = total_expenses * credit_spend_pct
    net_reduction = credit_contribution - monthly_credit_reuse
    total_balance = sum(c["balance"] for c in st.session_state.cards.values())
    weighted_apr = sum(c["balance"] * c["apr"] for c in st.session_state.cards.values()) / total_balance if total_balance > 0 else 0
    monthly_rate = weighted_apr / 12

    # Simulate payoff
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

    st.markdown("### 📉 Monthly Credit Behavior")
    col1, col2 = st.columns(2)
    col1.metric("Reused on Credit", f"${monthly_credit_reuse:,.2f}")
    col2.metric("Net Reduction", f"${net_reduction:,.2f}")
    if net_reduction <= 0:
        st.warning("⚠️ You're adding more than you're reducing.")

    if months_to_payoff:
        st.markdown("### 📈 Payoff Projection")
        st.line_chart(pd.Series(balances, name="Projected Balance"))

    st.markdown("### 🧮 Final Results")
    col1, col2, col3 = st.columns(3)
    col1.metric("Net Income", f"${monthly_net_income:,.2f}")
    col2.metric("After Expenses", f"${income_after_expenses:,.2f}")
    col3.metric("Contribution", f"${credit_contribution:,.2f}")
    if months_to_payoff:
        st.success(f"✅ Estimated Payoff Time: **{months_to_payoff} months** at {weighted_apr * 100:.2f}% APR")
    else:
        st.error("❌ You're not paying down your balance. Adjust your expenses or reserve %.")

    st.markdown("---")

    # AI Budget Coaching Section
    st.markdown("### 🧐 AI Budget Coaching")
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

    st.markdown("### 💬 Ask a Custom Question")
user_question = st.text_area("What do you want to ask about your finances, debt, or plan?")

if st.button("Ask GPT"):
    if user_question.strip():
        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a strategic and practical financial advisor who specializes in debt, credit cards,home lending and budgeting."},
                        {"role": "user", "content": user_question}
                    ],
                    temperature=0.6
                )
                answer = response.choices[0].message.content
                st.success(answer)
            except Exception as e:
                st.error(f"❌ GPT Error: {e}")

st.caption("Built with ❤️ by Ryan Worthington • © 2025 Pay’d")
