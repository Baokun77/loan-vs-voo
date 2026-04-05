import pandas as pd

COL_BUY = "buy_v"
COL_RENT = "rent_v"


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
                COL_BUY: round(buy_total, 2),
                COL_RENT: round(rent_voo, 2),
            }
        )

    eq_end = v - bal
    return pd.DataFrame(rows), eq_end, eq_end + buy_voo, rent_voo, pay
