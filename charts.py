from collections.abc import Callable

import altair as alt
import pandas as pd

from simulation import COL_BUY, COL_RENT


def wealth_paths_chart(df: pd.DataFrame, T: Callable[..., str]) -> alt.Chart:
    lb = T("legend_buy")
    lr = T("legend_rent")
    plot = df[["month", COL_BUY, COL_RENT]].rename(columns={COL_BUY: lb, COL_RENT: lr})
    plot["diff_br"] = plot[lb] - plot[lr]
    plot["hover_y"] = (plot[lb] + plot[lr]) / 2

    def cmp_row(r):
        d = r["diff_br"]
        b, z = r[lb], r[lr]
        if d > 0:
            lead = T("cmp_buy_hi")
        elif d < 0:
            lead = T("cmp_rent_hi")
        else:
            lead = T("cmp_tie")
        return T(
            "cmp_fmt",
            m=int(r["month"]),
            b=f"{b:,.2f}",
            z=f"{z:,.2f}",
            d=f"{d:+,.2f}",
            lead=lead,
        )

    plot["cmp_tip"] = plot.apply(cmp_row, axis=1)

    plot["yr"] = plot["month"] / 12.0
    mmax = int(plot["month"].max())
    ny = max(1, (mmax + 11) // 12)
    if ny <= 20:
        tick_yr = [float(y) for y in range(1, ny + 1)]
    else:
        step = max(1, ny // 8)
        tick_yr = list(range(1, ny + 1, step))
        if tick_yr[-1] != ny:
            tick_yr.append(ny)
        tick_yr = [float(y) for y in tick_yr]

    x_enc = alt.X(
        "yr:Q",
        title=T("ax_year"),
        axis=alt.Axis(values=tick_yr),
    )

    long_df = plot.melt(
        id_vars=["month", "yr"],
        value_vars=[lb, lr],
        var_name="series",
        value_name="wealth",
    )
    line = (
        alt.Chart(long_df)
        .mark_line(strokeWidth=2)
        .encode(
            x_enc,
            alt.Y("wealth:Q", title=T("ax_wealth"), scale=alt.Scale(zero=False)),
            alt.Color(
                "series:N",
                title="",
                scale=alt.Scale(range=["#2d5a3d", "#c45c26"]),
            ),
        )
    )
    hover = (
        alt.Chart(plot)
        .mark_point(size=100, opacity=0)
        .encode(
            x_enc,
            alt.Y(
                "hover_y:Q",
                scale=alt.Scale(zero=False),
                axis=alt.Axis(labels=False, title=None),
            ),
            tooltip=[
                alt.Tooltip("month:Q", title=T("tt_month")),
                alt.Tooltip(f"{lb}:Q", title=T("tt_buy"), format=",.2f"),
                alt.Tooltip(f"{lr}:Q", title=T("tt_rent"), format=",.2f"),
                alt.Tooltip("diff_br:Q", title=T("tt_diff"), format=",.2f"),
                alt.Tooltip("cmp_tip:N", title=T("tt_cmp")),
            ],
        )
    )
    return (
        (line + hover)
        .resolve_scale(y="shared")
        .properties(height=420)
        .configure_legend(orient="top")
        .interactive()
    )
