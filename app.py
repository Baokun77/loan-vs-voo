import altair as alt
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
                "买房：房产 + 省下的钱买 VOO": round(buy_total, 2),
                "租房：首付入市 + 省下的钱买 VOO": round(rent_voo, 2),
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
    f"买房加投VOO（第 {hold_years} 年）总财富",
    f"${buy_total_end:,.2f}",
    help="自住房产净值 + 若每月房租比买房现金支出更贵，则把「多出来的房租」当成同等金额坚持买 VOO 的账户。",
)
c2.metric(
    f"租房加投VOO（第 {hold_years} 年）总财富",
    f"${rent_voo_end:,.2f}",
    help="一开始把本应付的首付和 Closing 全部买 VOO；若每月买房现金支出比房租更贵，把差额继续买 VOO。",
)
c3.metric(
    f"买房加投VOO和租房加投VOO的财富差（第 {hold_years} 年结束时）",
    f"${buy_total_end - rent_voo_end:,.2f}",
    help="买房总财富 − 租房总财富；正数表示在设定的持有年数结束时，买房这条线更富。",
)

st.caption(
    "规则简述：租房线 — 首付与 Closing 先投入 VOO；之后只要「买房月供+税+HOA+维修+保险−利息抵税」高于房租，"
    " 就把差额继续投进 VOO。买房线 — 持有房产；只要房租高于上述买房现金支出，就把差额当作同步买 VOO 的储蓄。"
    " 未计卖房佣金、资本利得税等。"
)

COL_BUY = "买房：房产 + 省下的钱买 VOO"
COL_RENT = "租房：首付入市 + 省下的钱买 VOO"
_plot = df[["month", COL_BUY, COL_RENT]].rename(
    columns={COL_BUY: "买房路径", COL_RENT: "租房路径"}
)
_plot["差额_买减租"] = _plot["买房路径"] - _plot["租房路径"]
_plot["hover_y"] = (_plot["买房路径"] + _plot["租房路径"]) / 2


def _cmp_row(r):
    d = r["差额_买减租"]
    b, z = r["买房路径"], r["租房路径"]
    if d > 0:
        lead = "此时买房路径（房产净值 + 按规则买 VOO）更高。"
    elif d < 0:
        lead = "此时租房路径（首付/Closing 入市 + 按规则买 VOO）更高。"
    else:
        lead = "此时两条路径总财富相同。"
    return (
        f"第 {int(r['month'])} 个月末：买房路径 ${b:,.2f}，租房路径 ${z:,.2f}，"
        f"差额（买−租）${d:+,.2f}。{lead}"
    )


_plot["对比说明"] = _plot.apply(_cmp_row, axis=1)

_mmax = int(_plot["month"].max())
_tick_vals = list(range(12, _mmax + 1, 12))
_x = alt.X(
    "month:Q",
    title="月份",
    axis=alt.Axis(values=_tick_vals),
)

_long = _plot.melt(
    id_vars=["month"],
    value_vars=["买房路径", "租房路径"],
    var_name="线路",
    value_name="财富",
)
_line = (
    alt.Chart(_long)
    .mark_line(strokeWidth=2)
    .encode(
        _x,
        alt.Y("财富:Q", title="财富 ($)", scale=alt.Scale(zero=False)),
        alt.Color(
            "线路:N",
            title="",
            scale=alt.Scale(range=["#4C78A8", "#F58518"]),
        ),
    )
)
_hover = (
    alt.Chart(_plot)
    .mark_point(size=100, opacity=0)
    .encode(
        _x,
        alt.Y(
            "hover_y:Q",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labels=False, title=None),
        ),
        tooltip=[
            alt.Tooltip("month:Q", title="月份"),
            alt.Tooltip("买房路径:Q", title="买房路径 ($)", format=",.2f"),
            alt.Tooltip("租房路径:Q", title="租房路径 ($)", format=",.2f"),
            alt.Tooltip("差额_买减租:Q", title="差额 买−租 ($)", format=",.2f"),
            alt.Tooltip("对比说明:N", title="对比含义"),
        ],
    )
)
_chart = (
    (_line + _hover)
    .resolve_scale(y="shared")
    .properties(height=420)
    .configure_legend(orient="top")
    .interactive()
)
st.altair_chart(_chart, use_container_width=True)

with st.expander("月供与「纯房子」值多少钱"):
    st.write(
        f"等额本息下，**仅本金+利息**月供约 **${monthly_pi:,.2f}**（不含税、保险、HOA、维修）。 "
        f"持有期结束（第 {hold_years} 年）若只算房子、不算任何股票：**${eq_end:,.2f}**（当时市价 − 剩余房贷）。"
    )
