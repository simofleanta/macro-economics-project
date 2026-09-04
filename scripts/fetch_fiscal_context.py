"""Download Romania's annual general government deficit (% of GDP) from
Eurostat and save it as the JSON file behind the fiscal-context chart."""

import json
import urllib.request

DATA_PATH = "docs/fiscal-deficit-data.json"

DEFICIT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "gov_10dd_edpt1?geo=RO&format=JSON&na_item=B9&sector=S13&unit=PC_GDP"
)


def fetch_eurostat_series(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
    idx_to_time = {v: k for k, v in data["dimension"]["time"]["category"]["index"].items()}
    rows = [(idx_to_time[int(i)], v) for i, v in data["value"].items()]
    rows.sort()
    return rows


rows = fetch_eurostat_series(DEFICIT_URL)
series = [{"year": y, "deficit_pct_gdp": v} for y, v in rows if y >= "2010"]

with open(DATA_PATH, "w") as f:
    json.dump({"series": series}, f, indent=2)

print(f"Deficit series: {len(series)} years, {series[0]['year']} - {series[-1]['year']}")
