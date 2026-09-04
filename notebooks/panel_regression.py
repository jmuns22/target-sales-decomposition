"""
Panel regression: comp_sales ~ is_Target * post_boycott
Reads annual (ex-fuel, Walmart; standard, Target) comp sales directly from
sources/citation_log.csv -- no hardcoded numbers here. Rerun this script if
the citation log changes; never hand-edit results.

Honest limitation, stated up front: the boycott began Feb 2025 (FY2025),
so with only FY2022-FY2025 data available, "post" period = 1 year per
company. This limits statistical power -- the interval will likely be wide.
That's a genuine finding about data availability, not a bug to hide.
"""

import csv
import re
from pathlib import Path

try:
    import statsmodels.formula.api as smf
    import pandas as pd
except ImportError:
    raise SystemExit(
        "Missing packages. Run: pip install pandas statsmodels"
    )

CITATION_LOG = Path(__file__).resolve().parent.parent / "sources" / "citation_log.csv"

# Boycott began Feb 2025. Post-boycott quarters: Target's Q1 FY2025 onward,
# Walmart's Q1 FY2026 onward (their fiscal year is offset by one calendar
# year in naming vs Target's -- Walmart "FY2026" and Target "FY2025" cover
# the same real-world calendar window here).
POST_BOYCOTT_TARGET_QUARTERS = {
    "Q1 FY2025", "Q2 FY2025", "Q3 FY2025", "Q4 FY2025",
    "Q1 FY2026", "Q2 FY2026", "Q3 FY2026", "Q4 FY2026",
}
POST_BOYCOTT_WALMART_QUARTERS = {
    "Q1 FY2026", "Q2 FY2026", "Q3 FY2026", "Q4 FY2026",
    "Q1 FY2027", "Q2 FY2027", "Q3 FY2027", "Q4 FY2027",
}


def pct_to_float(value_str):
    match = re.search(r"(-?\d+\.?\d*)%", value_str)
    if not match:
        raise ValueError(f"Could not parse a percentage out of: '{value_str}'")
    return float(match.group(1))


def load_quarterly_panel():
    with open(CITATION_LOG, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    records = []
    for r in rows:
        if r["metric"] not in ("comp_sales_growth", "walmart_comp_sales_growth"):
            continue
        if "(annual)" in r["fiscal_period"]:
            continue  # annual rows excluded -- quarterly grain only

        # Extract a clean "Q# FY####" label from the fiscal_period text,
        # ignoring any trailing parenthetical naming notes.
        q_match = re.match(r"(Q[1-4] FY\d{4})", r["fiscal_period"].strip())
        if not q_match:
            continue  # skip anything that doesn't cleanly parse (e.g. EPS rows)
        quarter_label = q_match.group(1)

        if r["metric"] == "comp_sales_growth":
            company = "Target"
            is_post = quarter_label in POST_BOYCOTT_TARGET_QUARTERS
        else:
            company = "Walmart"
            is_post = quarter_label in POST_BOYCOTT_WALMART_QUARTERS

        records.append({
            "quarter": quarter_label,
            "company": company,
            "comp_sales": pct_to_float(r["value"]),
            "post": int(is_post),
        })

    return pd.DataFrame(records)


def main():
    df = load_quarterly_panel()

    if df.empty:
        raise SystemExit(
            "No quarterly rows found. Check citation_log.csv formatting."
        )

    df["is_Target"] = (df["company"] == "Target").astype(int)

    print("=" * 70)
    print("PANEL DATA USED (quarterly)")
    print("=" * 70)
    print(df.sort_values(["company", "quarter"]).to_string(index=False))
    print()
    print(f"n = {len(df)} observations")
    print(f"  Target quarters: {df[df['company']=='Target'].shape[0]}")
    print(f"  Walmart quarters: {df[df['company']=='Walmart'].shape[0]}")
    print(f"  Post-boycott observations: {df['post'].sum()}")
    print(f"  Pre-boycott observations: {(df['post']==0).sum()}")
    print()
    print("NOTE: this panel has known gaps (see README/citation_log for which")
    print("quarters are missing) -- it is not a complete, evenly-balanced panel.")
    print("Treat results as indicative given current public data, not final.")
    print()

    model = smf.ols("comp_sales ~ is_Target * post", data=df).fit()

    print("=" * 70)
    print("REGRESSION RESULTS: comp_sales ~ is_Target * post")
    print("=" * 70)
    print(model.summary())
    print()

    interaction_coef = model.params.get("is_Target:post")
    interaction_pval = model.pvalues.get("is_Target:post")
    ci = model.conf_int().loc["is_Target:post"] if "is_Target:post" in model.params.index else None

    print("=" * 70)
    print("DIFF-IN-DIFF ESTIMATE (the number that matters)")
    print("=" * 70)
    if interaction_coef is not None:
        print(f"  Coefficient (is_Target:post): {interaction_coef:.2f} percentage points")
        print(f"  p-value: {interaction_pval:.3f}")
        if ci is not None:
            print(f"  95% CI: [{ci[0]:.2f}, {ci[1]:.2f}] pp")
        print()
        if interaction_pval < 0.05:
            print("  Statistically significant at the 5% level.")
        else:
            print("  NOT statistically significant at the 5% level.")
            print(f"  With n={len(df)} observations and "
                  f"{df['post'].sum()} post-boycott observations, the")
            print("  confidence interval is wide. State this honestly rather than")
            print("  treating the point estimate as proof. More post-boycott")
            print("  quarters, as they're reported, would narrow this further.")
    else:
        print("  Could not extract interaction term -- check model specification.")


if __name__ == "__main__":
    main()
