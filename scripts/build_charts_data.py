"""Recompute the JSON data files consumed by the two interactive charts in
docs/, using a rolling window anchored to the latest available data (instead
of a fixed date range) so the published charts stay current when this script
is re-run on a schedule."""

import json
import sqlite3

import pandas as pd
from scipy import stats

DB_PATH = "output/bvb.db"
WINDOW_MONTHS = 60  # trailing 5 years for the nominal-vs-real chart
WINDOW_YEARS = 5  # trailing 5 years for the highlighted regression scatter
SENSITIVITY_MIN_YEARS = 4
SENSITIVITY_MAX_YEARS = 10

conn = sqlite3.connect(DB_PATH)
mv = pd.read_sql("SELECT * FROM monthly_nominal_vs_real ORDER BY symbol, month", conn)
inflation = pd.read_sql("SELECT * FROM inflation_ro ORDER BY month", conn)
conn.close()

symbols = sorted(mv["symbol"].unique())

# ---------- Chart 1: nominal vs real, trailing WINDOW_MONTHS ----------
series = {}
for symbol in symbols:
    g = mv[mv["symbol"] == symbol].sort_values("month").tail(WINDOW_MONTHS).copy()
    base_nominal = g["nominal_price"].iloc[0]
    base_real = g["real_price"].iloc[0]
    nominal_idx = (g["nominal_price"] / base_nominal * 100).round(2).tolist()
    real_idx = (g["real_price"] / base_real * 100).round(2).tolist()
    series[symbol] = {
        "months": g["month"].tolist(),
        "nominal_idx": nominal_idx,
        "real_idx": real_idx,
        "final_nominal_pct": round(nominal_idx[-1] - 100, 1),
        "final_real_pct": round(real_idx[-1] - 100, 1),
    }

start_month, end_month = series[symbols[0]]["months"][0], series[symbols[0]]["months"][-1]
hicp = pd.read_csv("output/hicp_index.csv").set_index("month")["hicp_index"]
cumulative_inflation_pct = round((hicp[end_month] / hicp[start_month] - 1) * 100, 1)
avg_gap_pp = round(
    sum(s["final_nominal_pct"] - s["final_real_pct"] for s in series.values()) / len(series), 1
)

chart1 = {
    "series": series,
    "meta": {
        "start_month": start_month,
        "end_month": end_month,
        "cumulative_inflation_pct": cumulative_inflation_pct,
        "avg_gap_pp": avg_gap_pp,
    },
}
with open("docs/real-vs-nominal-data.json", "w") as f:
    json.dump(chart1, f)
print(f"real-vs-nominal-data.json: {len(symbols)} symbols, {start_month} - {end_month}, "
      f"cumulative inflation {cumulative_inflation_pct}%")

# ---------- Chart 2: regression scatter + sensitivity ----------
mv["year"] = mv["month"].str[:4].astype(int)
inflation["year"] = inflation["month"].str[:4].astype(int)
inflation_year = (
    inflation.groupby("year")["inflation_yoy_pct"].mean().reset_index()
    .rename(columns={"inflation_yoy_pct": "avg_inflation_pct"})
)

dec = mv[mv["month"].str.endswith("-12")].sort_values(["symbol", "year"]).copy()
dec["nominal_ret_yr"] = dec.groupby("symbol")["nominal_price"].pct_change() * 100
dec["real_ret_yr"] = dec.groupby("symbol")["real_price"].pct_change() * 100
dec = dec.dropna(subset=["nominal_ret_yr"])
annual = dec.merge(inflation_year, on="year", how="left")
max_year = annual["year"].max()


def regression_line(x, y):
    r = stats.linregress(x, y)
    xs = [float(min(x)), float(max(x))]
    ys = [r.slope * xv + r.intercept for xv in xs]
    return {"x": xs, "y": ys, "slope": round(r.slope, 3), "intercept": round(r.intercept, 3),
            "r2": round(r.rvalue ** 2, 3), "p": round(r.pvalue, 4)}


window = annual[annual["year"] >= max_year - WINDOW_YEARS + 1]
scatter_points = window[["symbol", "year", "avg_inflation_pct", "nominal_ret_yr", "real_ret_yr"]].round(2).to_dict("records")
nominal_line = regression_line(window["avg_inflation_pct"].values, window["nominal_ret_yr"].values)
real_line = regression_line(window["avg_inflation_pct"].values, window["real_ret_yr"].values)

sensitivity = []
for k in range(SENSITIVITY_MIN_YEARS, SENSITIVITY_MAX_YEARS + 1):
    min_year = max_year - k + 1
    sub = annual[annual["year"] >= min_year]
    if sub["year"].nunique() < 2:
        continue
    rn = stats.linregress(sub["avg_inflation_pct"], sub["nominal_ret_yr"])
    rr = stats.linregress(sub["avg_inflation_pct"], sub["real_ret_yr"])
    sensitivity.append({
        "k": k, "years": f"{min_year}-{max_year}", "n": int(len(sub)),
        "p_nominal": round(rn.pvalue, 4), "p_real": round(rr.pvalue, 4),
        "r2_nominal": round(rn.rvalue ** 2, 3), "r2_real": round(rr.rvalue ** 2, 3),
    })

chart2 = {
    "scatter_points": scatter_points,
    "nominal_line": nominal_line,
    "real_line": real_line,
    "sensitivity": sensitivity,
    "window_years": f"{max_year - WINDOW_YEARS + 1}-{max_year}",
}
with open("docs/inflation-regression-data.json", "w") as f:
    json.dump(chart2, f)
print(f"inflation-regression-data.json: window {chart2['window_years']}, "
      f"{len(scatter_points)} points, {len(sensitivity)} sensitivity rows")
