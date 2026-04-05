import streamlit as st
import pandas as pd

# IRS federal ordinary income marginal rates (tax year 2025); no 20% bracket.
# Bracket dollar thresholds: https://www.irs.gov/filing/federal-income-tax-rates-and-brackets
FED_MARGINAL_LABELS = [
    "0% — 不模拟利息抵扣",
    "10%",
    "12%",
    "22%",
    "24%",
    "32%",
    "35%",
    "37%",
]
FED_MARGINAL_RATES = [0.0, 0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]


def simulate(
    price,
    down_pct,
    closing_pct,
    annual_rate,
    loan_years,
    hold_years,
    hoa_monthly,
    appreciation,
    prop_tax_rate,
    maint_pct,
    insurance_annual,
    marginal_rate,
    rent_monthly,
    rent_inflation,
    voo_annual,
    fee_annual,
):
    down = price * down_pct
    closing = price * closing_pct
    loan = price - down
    n_loan = loan_years * 12
    n_hold = hold_years * 12
    r = annual_rate / 12
    if loan <= 0:
        pay = 0.0
    elif n_loan <= 0:
        pay = 0.0
    elif r == 0:
        pay = loan / n_loan
    else:
        pay = loan * (r * (1 + r) ** n_loan) / ((1 + r) ** n_loan - 1)

    voo_net = voo_annual - fee_annual
    rm = (1 + voo_net) ** (1 / 12) - 1

    bal = loan
    port = down + closing
    rows = []

    for m in range(n_hold):
        v = price * (1 + appreciation) ** ((m + 1) / 12)
        if bal > 1e-9:
            interest = bal * r
            principal = min(max(pay - interest, 0), bal)
            bal -= principal
            pi_cash = principal + interest
        else:
            interest = 0
            pi_cash = 0
            bal = 0

        tax_m = v * prop_tax_rate / 12
        ins_m = insurance_annual / 12
        maint_m = v * maint_pct / 12
        own_gross = pi_cash + tax_m + ins_m + hoa_monthly + maint_m
        own_net = own_gross - interest * marginal_rate

        y = m // 12
        rent_m = rent_monthly * (1 + rent_inflation) ** y
        add = abs(own_net - rent_m)

        port = port * (1 + rm) + add
        equity = v - bal
        rows.append({"month": m + 1, "equity": equity, "voo": port})

    return pd.DataFrame(rows), v - bal, port, pay


st.set_page_config(page_title="买房 vs 租房投 VOO", layout="wide")
st.title("买房 vs 租房投 VOO")

with st.sidebar:
    st.markdown(
        """
        <style>
        div[data-testid="stSidebar"] [data-testid="stSlider"] {
            margin-bottom: 1.15rem;
            padding-bottom: 0.4rem;
        }
        div[data-testid="stSidebar"] [data-testid="stNumberInput"] {
            margin-bottom: 1.15rem;
            padding-bottom: 0.4rem;
        }
        div[data-testid="stSidebar"] h2 {
            margin-top: 0.35rem;
            margin-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header("房价与贷款")
    price = st.number_input("房价 ($)", min_value=50_000, value=1_800_000, step=50_000)
    down_pct_ui = st.slider("首付比例", 5, 50, 20, 1, format="%d%%")
    closing_pct_ui = st.slider("Closing 占房价", 0.0, 5.0, 1.5, 0.1, format="%.1f%%")
    annual_rate_ui = st.slider("房贷利率（年化）", 0.0, 12.0, 3.0, 0.1, format="%.1f%%")
    loan_years = st.slider("贷款年数（本息）", 1, 40, 30, 1)
    hold_years = st.slider("模拟持有年数", 1, 40, 30, 1)
    st.divider()

    st.header("持有成本")
    hoa_monthly = st.number_input("HOA（月）($)", min_value=0, value=400, step=50)
    appreciation_ui = st.slider("房价年化增值", -5.0, 15.0, 4.0, 0.5, format="%.1f%%")
    prop_tax_ui = st.slider("房产税有效税率 / 年（占市价）", 0.0, 3.0, 1.2, 0.1, format="%.1f%%")
    maint_ui = st.slider("维修占房价 / 年", 0.0, 4.0, 1.0, 0.25, format="%.2f%%")
    insurance_annual = st.number_input("房屋保险（年）($)", min_value=0, value=1800, step=100)
    st.divider()

    st.header("税务")
    _mi = st.selectbox(
        "联邦 ordinary 边际税率（抵房贷利息）",
        range(len(FED_MARGINAL_LABELS)),
        index=4,
        format_func=lambda i: FED_MARGINAL_LABELS[i],
        help="IRS 联邦所得税 ordinary income 挡位（2025：10/12/22/24/32/35/37%）。不含州税；标准扣除是否更优未建模。",
    )
    marginal_rate = FED_MARGINAL_RATES[_mi]
    st.divider()

    st.header("租房与通胀")
    rent_monthly = st.number_input("月租 — 起租 ($)", min_value=0, value=3600, step=100)
    rent_infl_ui = st.slider("房租年涨幅（对齐通胀）", 0.0, 10.0, 3.0, 0.5, format="%.1f%%")
    st.divider()

    st.header("VOO")
    voo_ui = st.slider("VOO 名义年化回报", -5.0, 20.0, 10.0, 0.5, format="%.1f%%")
    fee_ui = st.slider("VOO 费率 / 年", 0.0, 1.0, 0.03, 0.01, format="%.2f%%")

    down_pct = down_pct_ui / 100.0
    closing_pct = closing_pct_ui / 100.0
    annual_rate = annual_rate_ui / 100.0
    appreciation = appreciation_ui / 100.0
    prop_tax_rate = prop_tax_ui / 100.0
    maint_pct = maint_ui / 100.0
    rent_inflation = rent_infl_ui / 100.0
    voo_annual = voo_ui / 100.0
    fee_annual = fee_ui / 100.0

df, eq_end, voo_end, monthly_pi = simulate(
    price,
    down_pct,
    closing_pct,
    annual_rate,
    loan_years,
    hold_years,
    hoa_monthly,
    appreciation,
    prop_tax_rate,
    maint_pct,
    insurance_annual,
    marginal_rate,
    rent_monthly,
    rent_inflation,
    voo_annual,
    fee_annual,
)

c1, c2, c3 = st.columns(3)
c1.metric("期末房产净值（市价 − 剩余本金）", f"${eq_end:,.0f}")
c2.metric("期末 VOO 市值", f"${voo_end:,.0f}")
c3.metric("差额（房产 − VOO）", f"${eq_end - voo_end:,.0f}")

st.caption(
    "VOO 路径：初始 = 首付 + Closing；每月追加 = |买房净现金流 − 当月房租|（哪边住房更省，"
    " 省下的差额都按同一规则投入 VOO）。不计卖出费用与资本利得税。"
)

chart = df.rename(columns={"equity": "房产净值", "voo": "VOO"})
st.line_chart(chart.set_index("month")[["房产净值", "VOO"]])

with st.expander("月供（本息）参考"):
    st.write(f"月供本金+利息约 **${monthly_pi:,.2f}**（未含税、保险、HOA、维修）")
