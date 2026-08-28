"""Regress each stock's annual (Dec-to-Dec) return on that year's average
inflation rate, and check how the result changes as more years of history
are included."""

import sqlite3

import pandas as pd
from scipy import stats

DB_PATH = "output/bvb.db"

conn = sqlite3.connect(DB_PATH)
mv = pd.read_sql("SELECT * FROM monthly_nominal_vs_real ORDER BY symbol, month", conn)
inflation = pd.read_sql("SELECT * FROM inflation_ro ORDER BY month", conn)
conn.close()

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
max_year = annual.year.max()

print("p-value by number of trailing years included:\n")
print(f"{'years':>12}{'n':>5}{'p (nominal)':>14}{'p (real)':>12}")
for k in range(4, 11):
    min_year = max_year - k + 1
    subset = annual[annual.year >= min_year]
    if subset["year"].nunique() < 2:
        continue
    rn = stats.linregress(subset["avg_inflation_pct"], subset["nominal_ret_yr"])
    rr = stats.linregress(subset["avg_inflation_pct"], subset["real_ret_yr"])
    print(f"{f'{min_year}-{max_year}':>12}{len(subset):>5}{rn.pvalue:>14.4f}{rr.pvalue:>12.4f}")
