import pandas as pd

from simulation import COL_BUY, COL_RENT, simulate


def _kw(**overrides):
    base = dict(
        price=500_000,
        down_pct=0.2,
        closing_pct=0.015,
        annual_rate=0.04,
        loan_years=30,
        hold_years=2,
        hoa_monthly=250,
        appreciation=0.03,
        prop_tax_rate=0.012,
        maint_pct=0.01,
        insurance_annual=1500,
        marginal_rate=0.22,
        rent_monthly=2300,
        rent_inflation=0.03,
        voo_annual=0.07,
        fee_annual=0.0003,
    )
    base.update(overrides)
    return base


def test_simulate_row_count_and_columns():
    df, *_ = simulate(**_kw(hold_years=3))
    assert len(df) == 36
    assert list(df.columns) == ["month", COL_BUY, COL_RENT]
    assert df["month"].tolist() == list(range(1, 37))


def test_zero_interest_monthly_payment():
    _, _, _, _, pay = simulate(**_kw(price=100_000, down_pct=0.2, annual_rate=0, hold_years=1))
    assert abs(pay - 80_000 / 360) < 1e-9


def test_loan_paid_off_equity_matches_value():
    df, eq_end, buy_total_end, _, _ = simulate(
        **_kw(
            price=400_000,
            down_pct=0.2,
            closing_pct=0,
            appreciation=0,
            hold_years=30,
            loan_years=30,
            rent_monthly=5000,
            rent_inflation=0,
            voo_annual=0,
            fee_annual=0,
        )
    )
    assert abs(eq_end - 400_000) < 1.0
    last_buy = df.iloc[-1][COL_BUY]
    assert abs(last_buy - buy_total_end) < 0.02


def test_full_down_no_loan():
    df, eq_end, buy_total_end, rent_voo_end, pay = simulate(
        **_kw(down_pct=1.0, closing_pct=0, hold_years=1, appreciation=0, voo_annual=0, fee_annual=0)
    )
    assert pay == 0.0
    assert abs(eq_end - 500_000) < 1e-6
    assert isinstance(df, pd.DataFrame)


def test_loan_years_zero_sets_pay_zero():
    _, _, _, _, pay = simulate(**_kw(loan_years=0, hold_years=1))
    assert pay == 0.0


def test_positive_rate_amortization_payment():
    loan = 100_000
    n = 360
    r = 0.04 / 12
    expected = loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    _, _, _, _, pay = simulate(
        **_kw(price=125_000, down_pct=0.2, annual_rate=0.04, loan_years=30, hold_years=1)
    )
    assert abs(pay - expected) < 1e-6


def test_rent_exceeds_own_net_adds_buy_voo():
    df, *_ = simulate(
        **_kw(
            rent_monthly=50_000,
            hoa_monthly=0,
            prop_tax_rate=0,
            maint_pct=0,
            insurance_annual=0,
            marginal_rate=0,
            appreciation=0,
            rent_inflation=0,
            voo_annual=0,
            fee_annual=0,
            hold_years=1,
        )
    )
    assert df.iloc[-1][COL_BUY] > df.iloc[0][COL_BUY]


def test_own_net_exceeds_rent_adds_rent_voo():
    df, *_ = simulate(
        **_kw(
            rent_monthly=0,
            marginal_rate=0,
            appreciation=0,
            rent_inflation=0,
            voo_annual=0,
            fee_annual=0,
            hold_years=1,
        )
    )
    assert df.iloc[-1][COL_RENT] > df.iloc[0][COL_RENT]


def test_own_net_equals_rent_tie_branch():
    pay = 80_000 / 360.0
    df, *_ = simulate(
        price=100_000,
        down_pct=0.2,
        closing_pct=0,
        annual_rate=0,
        loan_years=30,
        hold_years=1,
        hoa_monthly=0,
        appreciation=0,
        prop_tax_rate=0,
        maint_pct=0,
        insurance_annual=0,
        marginal_rate=0,
        rent_monthly=pay,
        rent_inflation=0,
        voo_annual=0,
        fee_annual=0,
    )
    assert len(df) == 12


def test_balance_zero_branch_after_payoff():
    df, *_ = simulate(
        **_kw(
            price=200_000,
            down_pct=0.2,
            closing_pct=0,
            annual_rate=0,
            loan_years=1,
            hold_years=2,
            hoa_monthly=0,
            appreciation=0,
            prop_tax_rate=0,
            maint_pct=0,
            insurance_annual=0,
            marginal_rate=0,
            rent_monthly=10_000,
            rent_inflation=0,
            voo_annual=0,
            fee_annual=0,
        )
    )
    assert len(df) == 24
