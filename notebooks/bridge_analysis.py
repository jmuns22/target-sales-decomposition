"""
Target Sales Decomposition — Bridge Analysis
Reads sourced figures from sources/citation_log.csv (never hardcodes them here)
and computes two bridges:
  1. Revenue bridge: Target vs Walmart relative-performance swing (diff-in-diff)
  2. Profit bridge: EPS growth decomposed into tariff-refund vs organic contribution

Every computed number is checked against a hand-verified constant from the
project's own documented math (see README once written). If a mismatch
appears, it is printed loudly, not silently ignored.
"""

import re
import csv
from pathlib import Path

CITATION_LOG = Path(__file__).resolve().parent.parent / "sources" / "citation_log.csv"

# Hand-verified constants (computed and rechecked twice by hand, see conversation log)
HAND_CHECK = {
    "target_swing_pp": 5.7,
    "walmart_swing_pp": -2.0,
    "diff_in_diff_pp": 7.7,
    "eps_refund_contribution_pp": 80.3,
    "eps_organic_pp": 20.0,
}

TOLERANCE = 0.15  # percentage points; catches real mismatches, not float noise


def pct_to_float(value_str):
    """Extract a signed percentage number from strings like '3.8%' or '2.6% (ex-fuel)'."""
    match = re.search(r"(-?\d+\.?\d*)%", value_str)
    if not match:
        raise ValueError(f"Could not parse a percentage out of: '{value_str}'")
    return float(match.group(1))


def load_rows():
    if not CITATION_LOG.exists():
        raise FileNotFoundError(f"Citation log not found at {CITATION_LOG}")
    with open(CITATION_LOG, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def find_row(rows, metric, fiscal_period_contains):
    matches = [
        r for r in rows
        if r["metric"] == metric and fiscal_period_contains in r["fiscal_period"]
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly 1 row for metric='{metric}' containing "
            f"'{fiscal_period_contains}' in fiscal_period, found {len(matches)}. "
            f"Check citation_log.csv for duplicates or missing rows."
        )
    return matches[0]


def check(label, computed, expected):
    diff = abs(computed - expected)
    status = "OK" if diff <= TOLERANCE else "MISMATCH — INVESTIGATE"
    print(f"  [{status}] {label}: computed={computed:.2f}pp, hand-check={expected:.2f}pp, diff={diff:.2f}pp")
    return diff <= TOLERANCE


def main():
    rows = load_rows()
    all_ok = True

    print("=" * 70)
    print("BRIDGE 1: Revenue — Target vs Walmart relative-performance swing")
    print("=" * 70)

    target_current = pct_to_float(find_row(rows, "comp_sales_growth", "FY2026")["value"])
    target_prior = pct_to_float(find_row(rows, "comp_sales_growth", "FY2025")["value"])
    walmart_current = pct_to_float(find_row(rows, "walmart_comp_sales_growth", "FY27")["value"])
    walmart_prior = pct_to_float(find_row(rows, "walmart_comp_sales_growth", "FY26")["value"])

    target_swing = target_current - target_prior
    walmart_swing = walmart_current - walmart_prior
    diff_in_diff = target_swing - walmart_swing

    print(f"  Target:  current={target_current}%  prior={target_prior}%  swing={target_swing:.1f}pp")
    print(f"  Walmart: current={walmart_current}%  prior={walmart_prior}%  swing={walmart_swing:.1f}pp")
    print(f"  Diff-in-diff (Target outperformance): {diff_in_diff:.1f}pp")
    print()
    all_ok &= check("Target swing", target_swing, HAND_CHECK["target_swing_pp"])
    all_ok &= check("Walmart swing", walmart_swing, HAND_CHECK["walmart_swing_pp"])
    all_ok &= check("Diff-in-diff", diff_in_diff, HAND_CHECK["diff_in_diff_pp"])

    print()
    print("=" * 70)
    print("BRIDGE 2: Profit — EPS growth, refund vs organic")
    print("=" * 70)

    eps_headline = pct_to_float(find_row(rows, "eps_growth_headline", "FY2026")["value"])
    eps_exrefund = pct_to_float(find_row(rows, "eps_growth_exrefund", "FY2026")["value"])
    refund_contribution = eps_headline - eps_exrefund

    print(f"  Headline EPS growth:      {eps_headline:.1f}%")
    print(f"  Ex-refund EPS growth:     {eps_exrefund:.1f}%")
    print(f"  Refund contribution:      {refund_contribution:.1f}pp of the {eps_headline:.1f}% total")
    print()
    all_ok &= check("Refund contribution", refund_contribution, HAND_CHECK["eps_refund_contribution_pp"])
    all_ok &= check("Organic (ex-refund)", eps_exrefund, HAND_CHECK["eps_organic_pp"])

    print()
    print("=" * 70)
    if all_ok:
        print("ALL CHECKS PASSED — code output matches hand-verified math.")
    else:
        print("!!! ONE OR MORE MISMATCHES FOUND — DO NOT USE OUTPUT UNTIL RESOLVED !!!")
    print("=" * 70)

    return {
        "target_swing_pp": target_swing,
        "walmart_swing_pp": walmart_swing,
        "diff_in_diff_pp": diff_in_diff,
        "eps_headline_pct": eps_headline,
        "eps_exrefund_pct": eps_exrefund,
        "eps_refund_contribution_pp": refund_contribution,
    }


if __name__ == "__main__":
    main()
