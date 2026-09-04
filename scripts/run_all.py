"""Run the full pipeline in order: fetch prices, fetch inflation, compute
real returns, then rebuild the JSON data files behind the two charts."""

import subprocess
import sys

STEPS = [
    "scripts/fetch_prices.py",
    "scripts/fetch_inflation.py",
    "scripts/fetch_fiscal_context.py",
    "scripts/build_nominal_vs_real.py",
    "scripts/build_charts_data.py",
    "scripts/build_price_volume_data.py",
    "scripts/build_heatmap_data.py",
]

for step in STEPS:
    print(f"\n=== {step} ===")
    subprocess.run([sys.executable, step], check=True)
