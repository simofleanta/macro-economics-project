"""Download Romania's monthly HICP inflation (year-on-year rate, and the
underlying index level) from Eurostat, and save it to the Excel workbook
and SQLite database."""

import json
import sqlite3
import urllib.request

import pandas as pd

START_MONTH = "2015-01"
XLSX_PATH = "output/BVB_historical_price_volume.xlsx"
DB_PATH = "output/bvb.db"

RATE_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "prc_hicp_manr?geo=RO&format=JSON&unit=RCH_A&coicop=CP00"
)
INDEX_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "prc_hicp_midx?geo=RO&format=JSON&coicop=CP00&unit=I15"
)


def fetch_eurostat_series(url, value_col):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
    idx_to_time = {v: k for k, v in data["dimension"]["time"]["category"]["index"].items()}
    rows = [(idx_to_time[int(i)], v) for i, v in data["value"].items()]
    df = pd.DataFrame(rows, columns=["month", value_col]).sort_values("month")
    return df[df["month"] >= START_MONTH].reset_index(drop=True)


inflation_rate = fetch_eurostat_series(RATE_URL, "inflation_yoy_pct")
hicp_index = fetch_eurostat_series(INDEX_URL, "hicp_index")

conn = sqlite3.connect(DB_PATH)
conn.execute("DROP TABLE IF EXISTS inflation_ro")
conn.execute("CREATE TABLE inflation_ro (month TEXT PRIMARY KEY, inflation_yoy_pct REAL)")
inflation_rate.to_sql("inflation_ro", conn, if_exists="append", index=False)
conn.commit()
conn.close()

with pd.ExcelWriter(XLSX_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    inflation_rate.to_excel(writer, sheet_name="Inflation_RO", index=False)

hicp_index.to_csv("output/hicp_index.csv", index=False)
print(f"Inflation rate: {len(inflation_rate)} months, {inflation_rate.month.min()} - {inflation_rate.month.max()}")
print(f"HICP index: {len(hicp_index)} months, {hicp_index.month.min()} - {hicp_index.month.max()}")
