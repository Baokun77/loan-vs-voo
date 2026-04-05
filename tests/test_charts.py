import pandas as pd

from charts import wealth_paths_chart
from simulation import COL_BUY, COL_RENT


def test_wealth_paths_chart_returns_chart():
    df = pd.DataFrame(
        {
            "month": [1, 12, 24],
            COL_BUY: [100.0, 110.0, 120.0],
            COL_RENT: [95.0, 105.0, 115.0],
        }
    )

    def T(k, **kw):
        return k

    ch = wealth_paths_chart(df, T)
    assert ch is not None


def test_wealth_paths_chart_cmp_buy_rent_tie():
    df = pd.DataFrame(
        {
            "month": [1, 2, 3],
            COL_BUY: [200.0, 100.0, 150.0],
            COL_RENT: [100.0, 200.0, 150.0],
        }
    )

    def T(k, **kw):
        return k

    ch = wealth_paths_chart(df, T)
    assert ch is not None


def test_wealth_paths_chart_short_horizon_ticks():
    df = pd.DataFrame(
        {
            "month": [1, 2, 3],
            COL_BUY: [1.0, 2.0, 3.0],
            COL_RENT: [3.0, 2.0, 1.0],
        }
    )

    def T(k, **kw):
        return k

    ch = wealth_paths_chart(df, T)
    assert ch is not None
