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
    rent_voo = down + closing
    buy_voo = 0.0
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
        if rent_m > own_net:
            add_rent = 0.0
            add_buy = rent_m - own_net
        elif own_net > rent_m:
            add_rent = own_net - rent_m
            add_buy = 0.0
        else:
            add_rent = 0.0
            add_buy = 0.0

        rent_voo = rent_voo * (1 + rm) + add_rent
        buy_voo = buy_voo * (1 + rm) + add_buy
        equity = v - bal
        buy_total = equity + buy_voo
        rows.append(
            {
                "month": m + 1,
                "买房：房产 + 省下的钱买 VOO": buy_total,
                "租房：首付入市 + 省下的钱买 VOO": rent_voo,
            }
        )

    eq_end = v - bal
    return pd.DataFrame(rows), eq_end, eq_end + buy_voo, rent_voo, pay


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
    price = st.number_input("房屋成交价（总价，美元）", min_value=50_000, value=1_800_000, step=50_000)
    down_pct_ui = st.slider("首付占房价多少（其余为贷款）", 5, 50, 20, 1, format="%d%%")
    closing_pct_ui = st.slider("过户杂费 Closing 占房价（律师/产权/登记等）", 0.0, 5.0, 1.5, 0.1, format="%.1f%%")
    annual_rate_ui = st.slider("按揭年利率（等额本息、固定利率假设）", 0.0, 12.0, 3.0, 0.1, format="%.1f%%")
    loan_years = st.slider("按揭分多少年还清（决定月供）", 1, 40, 30, 1)
    hold_years = st.slider("打算持有这套房多少年（对比区间）", 1, 40, 30, 1)
    st.divider()

    st.header("持有成本（自住）")
    hoa_monthly = st.number_input("HOA / 物业费（每月，美元）", min_value=0, value=400, step=50)
    appreciation_ui = st.slider("假设房子每年涨价多少（复利）", -5.0, 15.0, 4.0, 0.5, format="%.1f%%")
    prop_tax_ui = st.slider("房产税简化：每年 = 市价 × 该比例（加州可再调低）", 0.0, 3.0, 1.2, 0.1, format="%.1f%%")
    maint_ui = st.slider("维修预留：每年约为市价的几成", 0.0, 4.0, 1.0, 0.25, format="%.2f%%")
    insurance_annual = st.number_input("房屋保险总保费（按年，美元）", min_value=0, value=1800, step=100)
    st.divider()

    st.header("税务")
    _mi = st.selectbox(
        "联邦所得税「工资 ordinary」边际税率 — 用来估算房贷利息能省多少税",
        range(len(FED_MARGINAL_LABELS)),
        index=4,
        format_func=lambda i: FED_MARGINAL_LABELS[i],
        help="按 IRS 联邦 ordinary income 七档（2025 无 20% 这一档）。未含州税；也未判断你该用标准扣除还是分项。",
    )
    marginal_rate = FED_MARGINAL_RATES[_mi]
    st.divider()

    st.header("若选择租房")
    rent_monthly = st.number_input("同等居住条件下，第一个月房租（美元）", min_value=0, value=3600, step=100)
    rent_infl_ui = st.slider("房租每年涨多少（按年跳档，类似通胀）", 0.0, 10.0, 3.0, 0.5, format="%.1f%%")
    st.divider()

    st.header("不买房时投股市（按 VOO 一类标普 500 ETF）")
    voo_ui = st.slider("假设股市长期名义年化回报（含分红、扣费前粗算）", -5.0, 20.0, 10.0, 0.5, format="%.1f%%")
    fee_ui = st.slider("ETF 管理费（每年占资产的比例，从上面回报里减掉）", 0.0, 1.0, 0.03, 0.01, format="%.2f%%")

    down_pct = down_pct_ui / 100.0
    closing_pct = closing_pct_ui / 100.0
    annual_rate = annual_rate_ui / 100.0
    appreciation = appreciation_ui / 100.0
    prop_tax_rate = prop_tax_ui / 100.0
    maint_pct = maint_ui / 100.0
    rent_inflation = rent_infl_ui / 100.0
    voo_annual = voo_ui / 100.0
    fee_annual = fee_ui / 100.0

df, eq_end, buy_total_end, rent_voo_end, monthly_pi = simulate(
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
c1.metric(
    "买房这条线期末总财富",
    f"${buy_total_end:,.0f}",
    help="自住房产净值 + 若每月房租比买房现金支出更贵，则把「多出来的房租」当成同等金额坚持买 VOO 的账户。",
)
c2.metric(
    "租房这条线期末总财富",
    f"${rent_voo_end:,.0f}",
    help="一开始把本应付的首付和 Closing 全部买 VOO；若每月买房现金支出比房租更贵，把差额继续买 VOO。",
)
c3.metric(
    "两条线相差多少",
    f"${buy_total_end - rent_voo_end:,.0f}",
    help="买房总财富 − 租房总财富；正数表示按本模型买房这条线期末更富。",
)

st.caption(
    "规则简述：租房线 — 首付与 Closing 先投入 VOO；之后只要「买房月供+税+HOA+维修+保险−利息抵税」高于房租，"
    " 就把差额继续投进 VOO。买房线 — 持有房产；只要房租高于上述买房现金支出，就把差额当作同步买 VOO 的储蓄。"
    " 未计卖房佣金、资本利得税等。"
)

_chart = df.set_index("month")[["买房：房产 + 省下的钱买 VOO", "租房：首付入市 + 省下的钱买 VOO"]]
st.line_chart(_chart)

with st.expander("月供与「纯房子」值多少钱"):
    st.write(
        f"等额本息下，**仅本金+利息**月供约 **${monthly_pi:,.2f}**（不含税、保险、HOA、维修）。 "
        f"期末若只算房子、不算任何股票：**${eq_end:,.0f}**（当时市价 − 剩余房贷）。"
    )
