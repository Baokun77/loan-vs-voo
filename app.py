import streamlit as st

from charts import wealth_paths_chart
from i18n import FED_MARGINAL_LABELS, FED_MARGINAL_RATES, I18N
from simulation import simulate

SIDEBAR_CSS = """
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
"""

if "lang" not in st.session_state:
    st.session_state.lang = "zh"

LANG = st.session_state.lang


def T(key, **kwargs):
    s = I18N[LANG][key]
    return s.format(**kwargs) if kwargs else s


st.set_page_config(page_title=T("page_title"), layout="wide")

_h1, _h2 = st.columns([5, 1])
with _h1:
    st.title(T("title"))
with _h2:
    st.write("")
    st.write("")
    if st.button(T("btn_lang"), key="lang_toggle"):
        st.session_state.lang = "en" if LANG == "zh" else "zh"
        st.rerun()

with st.sidebar:
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    st.header(T("hdr_loan"))
    price = st.number_input(T("price"), min_value=50_000, value=1_800_000, step=50_000)
    down_pct_ui = st.slider(T("down"), 5, 50, 20, 1, format="%d%%")
    closing_pct_ui = st.slider(T("closing"), 0.0, 5.0, 1.5, 0.1, format="%.1f%%")
    annual_rate_ui = st.slider(T("rate"), 0.0, 12.0, 3.0, 0.1, format="%.1f%%")
    loan_years = st.slider(T("loan_years"), 1, 40, 30, 1)
    hold_years = st.slider(T("hold_years"), 1, 40, 30, 1)
    st.divider()

    st.header(T("hdr_cost"))
    hoa_monthly = st.number_input(T("hoa"), min_value=0, value=400, step=50)
    appreciation_ui = st.slider(T("apprec"), -5.0, 15.0, 4.0, 0.5, format="%.1f%%")
    prop_tax_ui = st.slider(T("prop_tax"), 0.0, 3.0, 1.2, 0.1, format="%.1f%%")
    maint_ui = st.slider(T("maint"), 0.0, 4.0, 1.0, 0.25, format="%.2f%%")
    insurance_annual = st.number_input(T("ins"), min_value=0, value=1800, step=100)
    st.divider()

    st.header(T("hdr_tax"))
    _labels = FED_MARGINAL_LABELS[LANG]
    _mi = st.selectbox(
        T("marginal"),
        range(len(_labels)),
        index=4,
        format_func=lambda i: _labels[i],
        help=T("marginal_help"),
    )
    marginal_rate = FED_MARGINAL_RATES[_mi]
    st.divider()

    st.header(T("hdr_rent"))
    rent_monthly = st.number_input(T("rent_m"), min_value=0, value=3600, step=100)
    rent_infl_ui = st.slider(T("rent_inf"), 0.0, 10.0, 3.0, 0.5, format="%.1f%%")
    st.divider()

    st.header(T("hdr_voo"))
    voo_ui = st.slider(T("voo_ret"), -5.0, 20.0, 10.0, 0.5, format="%.1f%%")
    fee_ui = st.slider(T("voo_fee"), 0.0, 1.0, 0.03, 0.01, format="%.2f%%")

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
    T("metric_buy", y=hold_years),
    f"${buy_total_end:,.2f}",
    help=T("metric_buy_h"),
)
c2.metric(
    T("metric_rent", y=hold_years),
    f"${rent_voo_end:,.2f}",
    help=T("metric_rent_h"),
)
c3.metric(
    T("metric_diff", y=hold_years),
    f"${buy_total_end - rent_voo_end:,.2f}",
    help=T("metric_diff_h"),
)

st.caption(T("caption"))

st.altair_chart(wealth_paths_chart(df, T), use_container_width=True)

with st.expander(T("exp_title")):
    st.write(
        T(
            "exp_body",
            pi=f"{monthly_pi:,.2f}",
            y=hold_years,
            eq=f"{eq_end:,.2f}",
        )
    )
