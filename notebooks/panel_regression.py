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

# FY2025 is the first fiscal year the boycott was active for a meaningful
# stretch (started Feb 2025, near the start of Target's fiscal year).
POST_BOYCOTT_YEARS = {"FY2025"}


def pct_to_float(value_str):
    match = re.search(r"(-?\d+\.?\d*)%", value_str)
    if not match:
        raise ValueError(f"Could not parse a percentage out of: '{value_str}'")
    return float(match.group(1))


def load_annual_panel():
    with open(CITATION_LOG, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    records = []
    for r in rows:
        if "(annual)" not in r["fiscal_period"]:
            continue
        year_match = re.search(r"FY(\d{4})", r["fiscal_period"])
        if not year_match:
            continue
        fiscal_year = f"FY{year_match.group(1)}"

        if r["metric"] == "comp_sales_growth":
            company = "Target"
        elif r["metric"] == "walmart_comp_sales_growth":
            company = "Walmart"
        else:
            continue

        records.append({
            "fiscal_year": fiscal_year,
            "company": company,
            "comp_sales": pct_to_float(r["value"]),
        })

    return pd.DataFrame(records)


def main():
    df = load_annual_panel()

    if df.empty:
        raise SystemExit(
            "No annual rows found. Check that citation_log.csv has rows "
            "with '(annual)' in the fiscal_period column."
        )

    df["is_Target"] = (df["company"] == "Target").astype(int)
    df["post"] = df["fiscal_year"].isin(POST_BOYCOTT_YEARS).astype(int)

    print("=" * 70)
    print("PANEL DATA USED")
    print("=" * 70)
    print(df.sort_values(["fiscal_year", "company"]).to_string(index=False))
    print()
    print(f"n = {len(df)} observations "
          f"({df['company'].nunique()} companies x {df['fiscal_year'].nunique()} years)")
    print(f"Post-boycott years included: {sorted(POST_BOYCOTT_YEARS)}")
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
            print("  With n=8 and only 1 post-period year, this is expected --")
            print("  state this honestly rather than treating the point estimate")
            print("  as proof. More post-boycott years of data would narrow this.")
    else:
        print("  Could not extract interaction term -- check model specification.")


if __name__ == "__main__":
    main()
