"""Download Romania's RRF (PNRR) financial flows from Eurostat: funds
received by year (grants vs. loans) and how those funds were used (capital
vs. current expenditure). Save as the JSON file behind the PNRR flows chart."""

import json
import urllib.request

DATA_PATH = "docs/pnrr-flows-data.json"

RECEIVED_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "gov_rrf_fa?geo=RO&format=JSON&na_item=F2R_F4R&stk_flow=TRN&unit=MIO_EUR"
)
USE_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "gov_rrf_use?geo=RO&format=JSON&unit=MIO_EUR"
)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def extract(data, extra_dims):
    """extra_dims: dict of dimension -> required category id, everything else
    must be a single-valued dimension (already filtered by the URL)."""
    dims = data["dimension"]
    idx_to_time = {v: k for k, v in dims["time"]["category"]["index"].items()}
    size = data["size"]
    dim_order = data["id"]
    time_pos = dim_order.index("time")

    def label_index(dname):
        return {v: k for k, v in dims[dname]["category"]["index"].items()}

    results = {}
    for flat_str, value in data["value"].items():
        flat = int(flat_str)
        coords = []
        remaining = flat
        for s in reversed(size):
            coords.append(remaining % s)
            remaining //= s
        coords.reverse()
        ok = True
        for dname, want in extra_dims.items():
            pos = dim_order.index(dname)
            idx_map = label_index(dname)
            if idx_map.get(coords[pos]) != want:
                ok = False
                break
        if not ok:
            continue
        year = idx_to_time[coords[time_pos]]
        results[year] = value
    return results


received_raw = fetch(RECEIVED_URL)
use_raw = fetch(USE_URL)

grants_by_year = extract(received_raw, {"fin_typ": "GRNT"})
loans_by_year = extract(received_raw, {"fin_typ": "LOAN"})
capital_by_year = extract(use_raw, {"fin_typ": "TOTAL", "na_item": "CAP"})
current_by_year = extract(use_raw, {"fin_typ": "TOTAL", "na_item": "CUR"})

years = sorted(set(grants_by_year) | set(loans_by_year))
received_series = [
    {
        "year": y,
        "grants_mio_eur": grants_by_year.get(y),
        "loans_mio_eur": loans_by_year.get(y),
    }
    for y in years
]

years2 = sorted(set(capital_by_year) | set(current_by_year))
use_series = [
    {
        "year": y,
        "capital_mio_eur": capital_by_year.get(y),
        "current_mio_eur": current_by_year.get(y),
    }
    for y in years2
]

with open(DATA_PATH, "w") as f:
    json.dump({"received": received_series, "use": use_series}, f, indent=2)

print(f"RRF funds received: {len(received_series)} years")
print(f"RRF use (capital vs current): {len(use_series)} years")
