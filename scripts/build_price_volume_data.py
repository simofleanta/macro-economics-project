"""Resample daily prices to weekly close + weekly summed volume, per stock,
for the price & volume panel in the dashboard."""

import json
import sqlite3

import pandas as pd

DB_PATH = "output/bvb.db"
NAMES = {"TLV": "Banca Transilvania", "SNN": "Nuclearelectrica", "EL": "Electrica",
         "SNG": "Romgaz", "SNP": "OMV Petrom"}
ORDER = ["SNP", "SNG", "EL", "TLV", "SNN"]

conn = sqlite3.connect(DB_PATH)
prices = pd.read_sql("SELECT symbol, date, close, volume FROM historical_prices", conn)
conn.close()
prices["date"] = pd.to_datetime(prices["date"])

out = {}
for symbol in ORDER:
    g = prices[prices.symbol == symbol].sort_values("date").set_index("date")
    weekly_close = g["close"].resample("W-FRI").last().dropna()
    weekly_volume = g["volume"].resample("W-FRI").sum().reindex(weekly_close.index).fillna(0)
    out[symbol] = {
        "name": NAMES[symbol],
        "dates": [d.strftime("%Y-%m-%d") for d in weekly_close.index],
        "close": [round(v, 2) for v in weekly_close.tolist()],
        "volume": [int(v) for v in weekly_volume.tolist()],
    }
    print(f"{symbol}: {len(out[symbol]['dates'])} weeks, "
          f"{out[symbol]['dates'][0]} - {out[symbol]['dates'][-1]}")

with open("docs/price-volume-data.json", "w") as f:
    json.dump(out, f)
