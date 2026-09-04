"""
Counterfactual forecast: what would Target's comp sales have looked like
in the post-boycott quarters if the pre-boycott trend had simply continued?

Method: Holt's linear trend exponential smoothing (trend, no seasonal
component). Seasonal component deliberately omitted -- with only 12
pre-boycott quarters, there isn't enough data to reliably estimate
quarterly seasonality (would need at least 2 full cycles, ideally more).
This is a real limitation, stated here rather than hidden by forcing a
seasonal fit that the data can't actually support.

Reads Target's quarterly comp sales directly from citation_log.csv.
Compares forecast (the "no boycott, no refund, trend just continues"
counterfactual) against actual reported post-boycott quarters.
"""

import csv
import re
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except ImportError:
    raise SystemExit("Missing packages. Run: pip install pandas numpy statsmodels")

CITATION_LOG = Path(__file__).resolve().parent.parent / "sources" / "citation_log.csv"

# Boycott began Feb 2025 -- Target's Q1 FY2025 is the first affected quarter.
PRE_BOYCOTT_CUTOFF = ("FY2024", 4)  # last clean pre-boycott quarter: Q4 FY2024


def pct_to_float(value_str):
    match = re.search(r"(-?\d+\.?\d*)%", value_str)
    if not match:
        raise ValueError(f"Could not parse a percentage out of: '{value_str}'")
    return float(match.group(1))


def quarter_sort_key(label):
    q_match = re.match(r"Q(\d) FY(\d{4})", label)
    q_num, year = int(q_match.group(1)), int(q_match.group(2))
    return (year, q_num)


def load_target_quarterly():
    with open(CITATION_LOG, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    records = []
    for r in rows:
        if r["metric"] != "comp_sales_growth":
            continue
        if "(annual)" in r["fiscal_period"]:
            continue
        q_match = re.match(r"(Q[1-4] FY\d{4})", r["fiscal_period"].strip())
        if not q_match:
            continue
        label = q_match.group(1)
        records.append({"quarter": label, "comp_sales": pct_to_float(r["value"])})

    df = pd.DataFrame(records).drop_duplicates(subset="quarter")
    df["sort_key"] = df["quarter"].apply(quarter_sort_key)
    df = df.sort_values("sort_key").reset_index(drop=True)
    return df


def main():
    df = load_target_quarterly()

    cutoff_key = (int(PRE_BOYCOTT_CUTOFF[0][2:]), PRE_BOYCOTT_CUTOFF[1])
    pre_df = df[df["sort_key"] <= cutoff_key].reset_index(drop=True)
    post_df = df[df["sort_key"] > cutoff_key].reset_index(drop=True)

    print("=" * 70)
    print("PRE-BOYCOTT TRAINING DATA")
    print("=" * 70)
    print(pre_df[["quarter", "comp_sales"]].to_string(index=False))
    print(f"\nn = {len(pre_df)} quarters used to fit the trend model")
    print()

    if len(pre_df) < 8:
        print("WARNING: fewer than 8 pre-period quarters. Trend estimate will")
        print("be highly uncertain. Proceeding, but flag this in the write-up.")
        print()

    series = pre_df["comp_sales"].values
    model = ExponentialSmoothing(series, trend="add", damped_trend=True, seasonal=None)
    fit = model.fit()

    n_forecast = len(post_df)
    point_forecast = fit.forecast(n_forecast)

    # Simulate to get an uncertainty band around the point forecast
    np.random.seed(42)
    sims = fit.simulate(nsimulations=n_forecast, repetitions=1000, error="add")
    lower = np.percentile(sims, 2.5, axis=1)
    upper = np.percentile(sims, 97.5, axis=1)

    print("=" * 70)
    print("COUNTERFACTUAL FORECAST vs ACTUAL")
    print("=" * 70)
    print(f"{'Quarter':<12}{'Forecast':>10}{'95% Low':>10}{'95% High':>10}{'Actual':>10}{'Gap':>10}")
    for i in range(n_forecast):
        actual = post_df.iloc[i]["comp_sales"]
        gap = actual - point_forecast[i]
        print(f"{post_df.iloc[i]['quarter']:<12}{point_forecast[i]:>10.2f}"
              f"{lower[i]:>10.2f}{upper[i]:>10.2f}{actual:>10.2f}{gap:>10.2f}")

    print()
    print("Gap = Actual minus Forecast. Positive gap means Target outperformed")
    print("what its own pre-boycott trend would have predicted; negative means")
    print("it underperformed that trend.")
    print()
    print("LIMITATION: forecast trained on only", len(pre_df), "quarters, no")
    print("seasonal component (insufficient data to estimate it reliably).")
    print("Treat the uncertainty band as a lower bound on true uncertainty,")
    print("not a tight, final estimate.")


if __name__ == "__main__":
    main()
