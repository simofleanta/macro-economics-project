# Macro-Economics Project — BVB Stocks vs. Romanian Inflation

A small applied-macroeconomics project: how much of the stock market gains on the
Bucharest Stock Exchange (BVB) are real, once Romania's inflation is accounted for —
and whether inflation statistically predicts annual stock returns.

## Interactive charts

- **[Nominal vs. Real Returns](https://simofleanta.github.io/macro-economics-project/real-vs-nominal.html)** — cumulative and monthly nominal vs. inflation-adjusted returns for 5 BVB stocks (2021–2025).
- **[Inflation-Return Regression](https://simofleanta.github.io/macro-economics-project/inflation-regression.html)** — scatter plots, regression lines, and a chart showing how statistical significance depends on the time horizon used.

## Data

- **Stock prices & volume**: daily OHLCV for 5 BVB-listed stocks — `TLV` (Banca
  Transilvania), `SNN` (Nuclearelectrica), `EL` (Electrica), `SNG` (Romgaz), `SNP`
  (OMV Petrom) — via [Yahoo Finance](https://finance.yahoo.com) (`yfinance`), up to
  11 years of history.
- **Inflation**: Romania's Harmonised Index of Consumer Prices (HICP), monthly,
  from [Eurostat](https://ec.europa.eu/eurostat) — both the year-on-year rate and
  the underlying index level (base 2015=100). Eurostat publishes inflation with a
  ~2-month reporting lag.

## Method

1. Download daily prices and compute month-end nominal prices per stock.
2. Deflate nominal prices by the HICP index (rebased to each stock's first
   available month) to get a "real" (inflation-adjusted) price series.
3. Compute annual (December-to-December) nominal and real returns per stock.
4. Regress annual return on that year's average inflation rate (OLS), both
   pooled across stocks and per stock.
5. Repeat the regression using an expanding trailing window (last 4, 5, 6, ...
   10 years) to check whether any relationship found is stable or an artifact
   of a short/unusual sample.

## Key findings

- Cumulative inflation, Aug 2021 – Dec 2025: **+44%**. Nominal stock price gains
  over the same period look large (+142% to +309% across the 5 stocks), but the
  real (inflation-adjusted) gains are much smaller (+68% to +184%).
- A regression of annual real return on average annual inflation is
  **statistically significant** (p ≈ 0.04) when using only the last 4–5 years
  (2021–2025) — but the relationship **disappears** (p > 0.15) once 6 or more
  years of history are included. The apparent relationship is mostly driven by
  the 2022 inflation shock, not a stable long-term pattern.

## Requirements

```
pip install -r requirements.txt
```

See [`requirements.txt`](requirements.txt) — needs `pandas`, `yfinance`, `scipy`,
`openpyxl`.

## Running it

Scripts run in this order, from the repo root (they write to an `output/` folder):

```
python scripts/fetch_prices.py
python scripts/fetch_inflation.py
python scripts/build_nominal_vs_real.py
python scripts/regression_analysis.py
```

- `fetch_prices.py` — downloads stock price/volume history, saves to
  `output/BVB_historical_price_volume.xlsx` and `output/bvb.db`
  (table `historical_prices`).
- `fetch_inflation.py` — downloads Romania's inflation data, saves to the same
  Excel workbook (`Inflation_RO` sheet) and database (table `inflation_ro`).
- `build_nominal_vs_real.py` — computes the inflation-adjusted price series,
  saves to the database (table `monthly_nominal_vs_real`).
- `regression_analysis.py` — runs the annual regression and prints the
  time-horizon sensitivity table.

## Repository structure

```
scripts/    data collection & analysis scripts
docs/       interactive charts (published via GitHub Pages)
output/     generated data (not tracked in git — created when scripts run)
```
