"""Deflate each stock's nominal monthly price by Romania's HICP index to get
its inflation-adjusted ("real") price, and save both series to SQLite."""

import sqlite3

import pandas as pd

DB_PATH = "output/bvb.db"

conn = sqlite3.connect(DB_PATH)
prices = pd.read_sql("SELECT symbol, date, close FROM historical_prices", conn)
hicp_index = pd.read_csv("output/hicp_index.csv")

prices["date"] = pd.to_datetime(prices["date"])
prices["month"] = prices["date"].dt.to_period("M").astype(str)
monthly = (
    prices.sort_values("date")
    .groupby(["symbol", "month"], as_index=False)
    .last()[["symbol", "month", "close"]]
    .rename(columns={"close": "nominal_price"})
)

merged = monthly.merge(hicp_index, on="month", how="inner").sort_values(["symbol", "month"])

results = []
for symbol, g in merged.groupby("symbol"):
    g = g.copy()
    base_hicp = g["hicp_index"].iloc[0]
    g["real_price"] = g["nominal_price"] * (base_hicp / g["hicp_index"])
    g["nominal_return_pct"] = (g["nominal_price"] / g["nominal_price"].iloc[0] - 1) * 100
    g["real_return_pct"] = (g["real_price"] / g["real_price"].iloc[0] - 1) * 100
    results.append(g)

result = pd.concat(results, ignore_index=True)
conn.execute("DROP TABLE IF EXISTS monthly_nominal_vs_real")
result.to_sql("monthly_nominal_vs_real", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print(f"Saved {len(result)} rows to monthly_nominal_vs_real")
