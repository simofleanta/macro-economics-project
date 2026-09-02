"""Compute month-over-month price return per stock, per calendar month, for
the monthly-returns heatmap panel in the dashboard."""

import json
import sqlite3

import pandas as pd

DB_PATH = "output/bvb.db"
NAMES = {"TLV": "Banca Transilvania", "SNN": "Nuclearelectrica", "EL": "Electrica",
         "SNG": "Romgaz", "SNP": "OMV Petrom"}
ORDER = ["SNP", "SNG", "EL", "TLV", "SNN"]

conn = sqlite3.connect(DB_PATH)
prices = pd.read_sql("SELECT symbol, date, close FROM historical_prices", conn)
conn.close()

prices["date"] = pd.to_datetime(prices["date"])
prices["month"] = prices["date"].dt.to_period("M").astype(str)
monthly = (
    prices.sort_values("date").groupby(["symbol", "month"], as_index=False).last()
    [["symbol", "month", "close"]]
)
monthly["ret"] = monthly.groupby("symbol")["close"].pct_change() * 100
monthly = monthly.dropna(subset=["ret"])
monthly["year"] = monthly["month"].str[:4].astype(int)
monthly["mon"] = monthly["month"].str[5:7].astype(int)

out = {}
for symbol in ORDER:
    g = monthly[monthly.symbol == symbol]
    years = sorted(g.year.unique().tolist())
    cells = [{"year": int(r.year), "month": int(r.mon), "ret": round(r.ret, 1)} for r in g.itertuples()]
    out[symbol] = {"name": NAMES[symbol], "years": years, "cells": cells}
    print(f"{symbol}: {years[0]}-{years[-1]}, {len(cells)} cells")

with open("docs/heatmap-data.json", "w") as f:
    json.dump(out, f)
