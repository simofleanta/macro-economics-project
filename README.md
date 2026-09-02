# Macro-Economics Project — BVB Stocks vs. Romanian Inflation

A small applied-macroeconomics project: how much of the stock market gains on the
Bucharest Stock Exchange (BVB) are real, once Romania's inflation is accounted for —
and whether inflation statistically predicts annual stock returns.

## Dashboard

**[simofleanta.github.io/macro-economics-project](https://simofleanta.github.io/macro-economics-project/)**
— one page, four views: company overview, price &amp; volume, monthly-returns
heatmap, and nominal-vs-real returns with the inflation regression. Refreshes
automatically — see [Keeping it up to date](#keeping-it-up-to-date).

The two return/regression charts are also available standalone:
[Nominal vs. Real Returns](https://simofleanta.github.io/macro-economics-project/real-vs-nominal.html) ·
[Inflation-Return Regression](https://simofleanta.github.io/macro-economics-project/inflation-regression.html)

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

(Illustrative, based on the most recent data refresh — see the live charts above
for current numbers, since these move as the trailing window rolls forward.)

- Nominal stock price gains over the trailing 5-year window look large (roughly
  +100% to +300% across the 5 stocks), but a large share of that is inflation:
  real (inflation-adjusted) gains are much smaller once the cumulative inflation
  over the same period (currently ~48%) is backed out.
- A regression of annual real return on average annual inflation is
  **statistically significant** (p ≈ 0.04) when using only the last 4–5 years —
  but the relationship **disappears** (p > 0.15) once 6 or more years of history
  are included. The apparent relationship is mostly driven by the 2022 inflation
  shock, not a stable long-term pattern.

## Requirements

```
pip install -r requirements.txt
```

See [`requirements.txt`](requirements.txt) — needs `pandas`, `yfinance`, `scipy`,
`openpyxl`.

## Running it

```
python scripts/run_all.py
```

runs the full pipeline in order (writes to an `output/` folder, and refreshes the
JSON files behind the dashboard in `docs/`). The steps, individually:

- `fetch_prices.py` — downloads stock price/volume history, saves to
  `output/BVB_historical_price_volume.xlsx` and `output/bvb.db`
  (table `historical_prices`).
- `fetch_inflation.py` — downloads Romania's inflation data, saves to the same
  Excel workbook (`Inflation_RO` sheet) and database (table `inflation_ro`).
  Must run after `fetch_prices.py` (it appends to the same workbook).
- `build_nominal_vs_real.py` — computes the inflation-adjusted price series,
  saves to the database (table `monthly_nominal_vs_real`).
- `build_charts_data.py` — recomputes `docs/real-vs-nominal-data.json` and
  `docs/inflation-regression-data.json` from a trailing window anchored to the
  latest available data, so the published charts stay current.
- `build_price_volume_data.py` — recomputes `docs/price-volume-data.json`
  (weekly close + weekly volume per stock, full history).
- `build_heatmap_data.py` — recomputes `docs/heatmap-data.json` (month-over-month
  price return per stock, full history).
- `regression_analysis.py` — standalone script that prints the annual
  regression and time-horizon sensitivity table to the console (not needed for
  the charts, useful for exploring the data directly).

## Keeping it up to date

A [GitHub Actions workflow](.github/workflows/refresh-data.yml) runs the full
pipeline automatically on the 1st of every month (and can be triggered manually
from the Actions tab) and commits the refreshed `docs/*-data.json` files. The
published charts read their data from those JSON files at load time, so they
update automatically after each run — no manual refresh needed.

## Repository structure

```
scripts/    data collection & analysis scripts
docs/       interactive charts + their data files (published via GitHub Pages)
output/     generated Excel/SQLite data (not tracked in git — created when scripts run)
.github/    the scheduled refresh workflow
```
