"""Download daily OHLCV price history for BVB-listed stocks from Yahoo Finance
and save it to an Excel workbook (one sheet per symbol) and a SQLite table."""

import sqlite3

import pandas as pd
import yfinance as yf

SYMBOLS = ["TLV", "SNN", "EL", "SNG", "SNP"]
PERIOD = "11y"
XLSX_PATH = "output/BVB_historical_price_volume.xlsx"
DB_PATH = "output/bvb.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("DROP TABLE IF EXISTS historical_prices")
conn.execute(
    """
    CREATE TABLE historical_prices (
        symbol TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        PRIMARY KEY (symbol, date)
    )
    """
)

with pd.ExcelWriter(XLSX_PATH, engine="openpyxl", mode="w") as writer:
    for symbol in SYMBOLS:
        df = yf.download(f"{symbol}.RO", period=PERIOD, progress=False)
        df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]].round(2)
        df.index.name = "Date"
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        df.to_excel(writer, sheet_name=symbol, index=False)

        db_df = df.copy()
        db_df.columns = ["date", "open", "high", "low", "close", "volume"]
        db_df.insert(0, "symbol", symbol)
        db_df.to_sql("historical_prices", conn, if_exists="append", index=False)
        print(f"{symbol}: {len(db_df)} rows, {db_df.date.min()} - {db_df.date.max()}")

conn.commit()
conn.close()
