"""
STANDALONE METHODOLOGY DEMO -- NOT TARGET DATA.

Uses a real public dataset (Kaggle: "Marketing A/B Testing" by faviovaz,
588k rows) to demonstrate A/B test analysis: significance testing, effect
size, and a power calculation. This proves the methodology, not access to
any Target-internal experiment, which doesn't exist and isn't claimed here.

Dataset: ad group (saw advertisement) vs psa group (saw public service
announcement / control), outcome = converted (bought the product or not).

Known limitation of this dataset, stated up front: groups are heavily
imbalanced (~96% ad, ~4% psa). This is a real property of the data, not
hidden -- the power analysis below quantifies what that imbalance costs
in terms of ability to detect a true effect.
"""

import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "marketing_AB.csv"


def main():
    if not DATA_PATH.exists():
        raise SystemExit(
            f"Dataset not found at {DATA_PATH}.\n"
            f"Download from https://www.kaggle.com/datasets/faviovaz/marketing-ab-testing\n"
            f"and place the CSV at data/marketing_AB.csv"
        )

    df = pd.read_csv(DATA_PATH)

    # Column names in this dataset use a space; normalize for convenience
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    if "test_group" not in df.columns or "converted" not in df.columns:
        raise SystemExit(
            f"Expected columns 'test group' and 'converted' not found. "
            f"Actual columns: {list(df.columns)}"
        )

    ad_group = df[df["test_group"] == "ad"]
    psa_group = df[df["test_group"] == "psa"]

    n_ad, n_psa = len(ad_group), len(psa_group)
    conv_ad = ad_group["converted"].sum()
    conv_psa = psa_group["converted"].sum()
    rate_ad = conv_ad / n_ad
    rate_psa = conv_psa / n_psa

    print("=" * 70)
    print("GROUP SUMMARY")
    print("=" * 70)
    print(f"  Ad group:  n={n_ad:,}   conversions={conv_ad:,}   rate={rate_ad:.4%}")
    print(f"  PSA group: n={n_psa:,}    conversions={conv_psa:,}    rate={rate_psa:.4%}")
    print(f"  Group split: {n_ad/(n_ad+n_psa):.1%} ad / {n_psa/(n_ad+n_psa):.1%} psa "
          f"(imbalanced -- known property of this dataset)")
    print()

    # Two-proportion z-test
    count = [conv_ad, conv_psa]
    nobs = [n_ad, n_psa]
    z_stat, p_value = proportions_ztest(count, nobs)

    print("=" * 70)
    print("SIGNIFICANCE TEST: two-proportion z-test")
    print("=" * 70)
    print(f"  H0: conversion rate is equal between ad and psa groups")
    print(f"  z-statistic: {z_stat:.3f}")
    print(f"  p-value: {p_value:.6f}")
    if p_value < 0.05:
        print("  Result: statistically significant at the 5% level.")
        print("  Reject H0 -- the ad group's conversion rate differs from psa's.")
    else:
        print("  Result: NOT statistically significant at the 5% level.")
    print()

    # Effect size (Cohen's h, standard for comparing two proportions)
    effect_size = proportion_effectsize(rate_ad, rate_psa)
    print("=" * 70)
    print("EFFECT SIZE: Cohen's h")
    print("=" * 70)
    print(f"  h = {effect_size:.4f}")
    if abs(effect_size) < 0.2:
        magnitude = "small"
    elif abs(effect_size) < 0.5:
        magnitude = "medium"
    else:
        magnitude = "large"
    print(f"  Magnitude: {magnitude} (by Cohen's conventional thresholds)")
    relative_lift = (rate_ad - rate_psa) / rate_psa
    print(f"  Relative lift: {relative_lift:+.1%} (ad vs psa conversion rate)")
    print()

    # Power analysis -- what does the imbalanced sample actually buy us?
    print("=" * 70)
    print("POWER ANALYSIS")
    print("=" * 70)
    power_analysis = NormalIndPower()
    achieved_power = power_analysis.power(
        effect_size=abs(effect_size), nobs1=n_psa, ratio=n_ad / n_psa, alpha=0.05
    )
    print(f"  Achieved statistical power at observed effect size: {achieved_power:.4f}")
    print(f"  (Power = probability of correctly detecting a true effect this size,")
    print(f"  given the actual group sizes and imbalance in this dataset.)")

    # What sample size per group WOULD be needed for 80% power at this effect size,
    # if groups were balanced 1:1 -- shows the cost of the imbalance
    required_n_balanced = power_analysis.solve_power(
        effect_size=abs(effect_size), power=0.8, ratio=1.0, alpha=0.05
    )
    print(f"  For comparison: a balanced (1:1) design would need only "
          f"~{required_n_balanced:.0f} per group for 80% power at this effect size --")
    print(f"  far fewer than the {n_psa:,} in the actual (smaller) psa group here.")


if __name__ == "__main__":
    main()
