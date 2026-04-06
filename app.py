import streamlit as st

from charts import wealth_paths_chart
from i18n import FED_MARGINAL_LABELS, FED_MARGINAL_RATES, I18N
from simulation import simulate

CSS = """
<style>
/* ── Sidebar ── */
section[data-testid="stSidebar"] > div:first-child {
    background-color: #e8f2ea;
}
section[data-testid="stSidebar"] [data-testid="stSlider"] {
    margin-bottom: 0.85rem;
    padding-bottom: 0.25rem;
}
section[data-testid="stSidebar"] [data-testid="stNumberInput"] {
    margin-bottom: 0.85rem;
    padding-bottom: 0.25rem;
}
section[data-testid="stSidebar"] [data-testid="stNumberInput"] button {
    display: none !important;
}
section[data-testid="stSidebar"] [data-testid="stNumberInput"] input {
    width: 100% !important;
    -moz-appearance: textfield;
}
section[data-testid="stSidebar"]
    [data-testid="stNumberInput"]
    input[type="number"]::-webkit-outer-spin-button,
section[data-testid="stSidebar"]
    [data-testid="stNumberInput"]
    input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}
section[data-testid="stSidebar"] h2 {
    margin-top: 0.2rem;
    margin-bottom: 0.4rem;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #3a6b46;
}
section[data-testid="stSidebar"] hr {
    margin: 0.6rem 0;
    border-color: #c4dfc8;
}

/* ── Main ── */
.block-container { padding-top: 1.25rem; }
div[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }

/* ── Metric cards ── */
.mc-wrap {
    border: 1.5px solid #d0e8d4;
    border-radius: 10px;
    padding: 18px 22px 16px;
    background: #ffffff;
    min-height: 92px;
}
.mc-wrap.dark {
    background: #2d5a3d;
    border-color: #2d5a3d;
}
.mc-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: #5a8a68;
    margin-bottom: 6px;
    line-height: 1.3;
}
.mc-wrap.dark .mc-label {
    color: #9fcfad;
}
.mc-value {
    font-size: 1.55rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: #111111;
    line-height: 1.15;
}
.mc-wrap.dark .mc-value {
    color: #ffffff;
}

/* ── Lang button ── */
div[data-testid="stButton"] > button {
    background-color: #2d5a3d !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    padding: 0.35rem 1.1rem !important;
}
div[data-testid="stButton"] > button:hover {
    background-color: #3a7050 !important;
    color: #ffffff !important;
    border: none !important;
}

@media (max-width: 768px) {
    .block-container [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    .block-container [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
    }
}
</style>
"""

BASE_PRESET = {
    "w_price": 1_800_000,
    "w_down": 20,
    "w_closing": 1.5,
    "w_rate": 3.0,
    "w_loan_y": 30,
    "w_hold_y": 30,
    "w_hoa": 400,
    "w_apprec": 4.0,
    "w_prop_tax": 1.2,
    "w_maint": 1.0,
    "w_ins": 1800,
    "w_marginal": 4,
    "w_rent": 3600,
    "w_rent_inf": 3.0,
    "w_voo": 10.0,
    "w_fee": 0.03,
}
PRESET_HI_RATE = {**BASE_PRESET, "w_rate": 6.5}
PRESET_SOFT = {**BASE_PRESET, "w_voo": 5.0, "w_apprec": 2.0}


def metric_card(label: str, value: str, dark: bool = False) -> str:
    cls = "mc-wrap dark" if dark else "mc-wrap"
    return (
        f'<div class="{cls}">'
        f'<div class="mc-label">{label}</div>'
        f'<div class="mc-value">{value}</div>'
        f"</div>"
    )


if "lang" not in st.session_state:
    st.session_state.lang = "zh"

LANG = st.session_state.lang


def T(key, **kwargs):
    s = I18N[LANG][key]
    return s.format(**kwargs) if kwargs else s


st.set_page_config(
    page_title=T("page_title"),
    layout="wide",
    page_icon="🏠",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
_h1, _h2 = st.columns([6, 1])
with _h1:
    st.title(T("title"))
with _h2:
    st.write("")
    if st.button(T("btn_lang"), key="lang_toggle"):
        st.session_state.lang = "en" if LANG == "zh" else "zh"
        st.rerun()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.caption(T("hdr_presets"))
    _pb, _ph, _ps = st.columns(3)
    with _pb:
        if st.button(T("preset_base"), key="btn_preset_base", use_container_width=True):
            for _k, _v in BASE_PRESET.items():
                st.session_state[_k] = _v
            st.rerun()
    with _ph:
        if st.button(T("preset_hi_rate"), key="btn_preset_hi", use_container_width=True):
            for _k, _v in PRESET_HI_RATE.items():
                st.session_state[_k] = _v
            st.rerun()
    with _ps:
        if st.button(T("preset_soft"), key="btn_preset_soft", use_container_width=True):
            for _k, _v in PRESET_SOFT.items():
                st.session_state[_k] = _v
            st.rerun()
    st.divider()

    _labels = FED_MARGINAL_LABELS[LANG]
    with st.expander(T("hdr_loan"), expanded=True):
        price = st.number_input(
            T("price"), min_value=50_000, value=1_800_000, step=50_000, key="w_price"
        )
        down_pct_ui = st.slider(T("down"), 5, 50, 20, 1, format="%d%%", key="w_down")
        closing_pct_ui = st.slider(
            T("closing"), 0.0, 5.0, 1.5, 0.1, format="%.1f%%", key="w_closing"
        )
        annual_rate_ui = st.slider(
            T("rate"), 0.0, 12.0, 3.0, 0.1, format="%.1f%%", key="w_rate"
        )
        loan_years = st.slider(T("loan_years"), 1, 40, 30, 1, key="w_loan_y")
        hold_years = st.slider(T("hold_years"), 1, 40, 30, 1, key="w_hold_y")

    with st.expander(T("hdr_cost"), expanded=False):
        hoa_monthly = st.number_input(T("hoa"), min_value=0, value=400, step=50, key="w_hoa")
        appreciation_ui = st.slider(
            T("apprec"), -5.0, 15.0, 4.0, 0.5, format="%.1f%%", key="w_apprec"
        )
        prop_tax_ui = st.slider(
            T("prop_tax"), 0.0, 3.0, 1.2, 0.1, format="%.1f%%", key="w_prop_tax"
        )
        maint_ui = st.slider(
            T("maint"), 0.0, 4.0, 1.0, 0.25, format="%.2f%%", key="w_maint"
        )
        insurance_annual = st.number_input(
            T("ins"), min_value=0, value=1800, step=100, key="w_ins"
        )

    with st.expander(T("hdr_tax"), expanded=False):
        _mi = st.selectbox(
            T("marginal"),
            range(len(_labels)),
            index=4,
            format_func=lambda i: _labels[i],
            help=T("marginal_help"),
            key="w_marginal",
        )
        marginal_rate = FED_MARGINAL_RATES[_mi]

    with st.expander(T("hdr_rent"), expanded=False):
        rent_monthly = st.number_input(
            T("rent_m"), min_value=0, value=3600, step=100, key="w_rent"
        )
        rent_infl_ui = st.slider(
            T("rent_inf"), 0.0, 10.0, 3.0, 0.5, format="%.1f%%", key="w_rent_inf"
        )

    with st.expander(T("hdr_voo"), expanded=False):
        voo_ui = st.slider(
            T("voo_ret"), -5.0, 20.0, 10.0, 0.5, format="%.1f%%", key="w_voo"
        )
        fee_ui = st.slider(T("voo_fee"), 0.0, 1.0, 0.03, 0.01, format="%.2f%%", key="w_fee")

down_pct = down_pct_ui / 100.0
closing_pct = closing_pct_ui / 100.0
annual_rate = annual_rate_ui / 100.0
appreciation = appreciation_ui / 100.0
prop_tax_rate = prop_tax_ui / 100.0
maint_pct = maint_ui / 100.0
rent_inflation = rent_infl_ui / 100.0
voo_annual = voo_ui / 100.0
fee_annual = fee_ui / 100.0

# ── Simulate ─────────────────────────────────────────────────────────────────
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

diff = buy_total_end - rent_voo_end

with st.expander(T("exp_assumptions_title"), expanded=False):
    st.markdown(T("exp_assumptions_body"))

if abs(diff) < 0.005:
    st.markdown(T("conclusion_tie", y=hold_years))
elif diff > 0:
    st.markdown(
        T("conclusion_buy", y=hold_years, d=f"{abs(diff):,.2f}"),
    )
else:
    st.markdown(
        T("conclusion_rent", y=hold_years, d=f"{abs(diff):,.2f}"),
    )

# ── Metric cards ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        metric_card(T("metric_buy", y=hold_years), f"${buy_total_end:,.2f}"),
        unsafe_allow_html=True,
    )
    st.caption(T("metric_buy_h"))
with c2:
    st.markdown(
        metric_card(T("metric_rent", y=hold_years), f"${rent_voo_end:,.2f}"),
        unsafe_allow_html=True,
    )
    st.caption(T("metric_rent_h"))
with c3:
    st.markdown(
        metric_card(T("metric_diff", y=hold_years), f"${diff:+,.2f}", dark=True),
        unsafe_allow_html=True,
    )
    st.caption(T("metric_diff_h"))

st.caption(T("caption"))

with st.expander(T("exp_formula_title")):
    st.markdown(T("exp_formula_intro"))
    st.markdown(T("exp_formula_c"))
    st.latex(
        r"r_m = (1 + g)^{1/12} - 1,\quad g = r_{\mathrm{VOO}} - f_{\mathrm{VOO}}"
    )
    st.latex(
        r"S_{t+1} = S_t(1+r_m) + \max(0,\, C_t - R_t),\quad S_0 = D"
    )
    st.latex(r"W_{\mathrm{rent}} = S_T")
    st.latex(
        r"B_{t+1} = B_t(1+r_m) + \max(0,\, R_t - C_t),\quad B_0 = 0"
    )
    st.latex(r"E_t = H_t - L_t")
    st.latex(r"W_{\mathrm{buy}} = E_T + B_T")
    st.caption(T("exp_formula_note"))

# ── Chart ─────────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.altair_chart(wealth_paths_chart(df, T), use_container_width=True)

# ── Expander ─────────────────────────────────────────────────────────────────
with st.expander(T("exp_title")):
    st.write(
        T(
            "exp_body",
            pi=f"{monthly_pi:,.2f}",
            y=hold_years,
            eq=f"{eq_end:,.2f}",
        )
    )
