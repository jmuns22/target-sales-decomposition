"""
Generates two standalone HTML charts from data/bridge_data.json:
  1. Slope chart — Target vs Walmart comp sales swing (Bridge 1)
  2. Waterfall — Target EPS growth decomposition (Bridge 2)

These are standalone proof-of-concept visuals, separate from the full
interactive dashboard shell (planned for later). No manual data entry here —
if source numbers change, rerun bridge_analysis.py first to regenerate
bridge_data.json, then rerun this script.
"""

import json
from pathlib import Path
import plotly.graph_objects as go

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "bridge_data.json"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "dashboard"

TARGET_RED = "#CC0000"
WALMART_BLUE = "#0071CE"
NEUTRAL_GRAY = "#7A7A7A"


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_slope_chart(bridge1):
    fig = go.Figure()

    colors = {"Target": TARGET_RED, "Walmart": WALMART_BLUE}

    for series in bridge1["series"]:
        periods = [p["period"] for p in series["points"]]
        values = [p["value_pct"] for p in series["points"]]
        fig.add_trace(go.Scatter(
            x=["Q2 2025", "Q2 2026"],
            y=values,
            mode="lines+markers+text",
            name=series["label"],
            line=dict(color=colors.get(series["label"], NEUTRAL_GRAY), width=3),
            marker=dict(size=10),
            text=[f"{v:+.1f}%" for v in values],
            textposition="top center",
        ))

    diff = bridge1["headline_stat"]["value_pp"]
    fig.update_layout(
        title=f"Comp Sales Swing: Target vs Walmart<br><sub>Target closed a {diff}pp competitive gap year-over-year</sub>",
        yaxis_title="Comparable Sales Growth (%)",
        xaxis=dict(showgrid=False),
        yaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor="lightgray"),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        width=800,
        height=500,
    )

    out_path = OUTPUT_DIR / "bridge1_slope_chart.html"
    fig.write_html(out_path)
    print(f"Bridge 1 slope chart written to: {out_path}")


def build_waterfall_chart(bridge2):
    steps = bridge2["steps"]
    labels = [s["label"] for s in steps]
    values = [s["value_pp"] for s in steps]
    measures = ["absolute" if s["type"] == "total" else "relative" for s in steps]

    fig = go.Figure(go.Waterfall(
        x=labels,
        y=values,
        measure=measures,
        text=[f"{v:+.1f}pp" for v in values],
        textposition="outside",
        connector=dict(line=dict(color=NEUTRAL_GRAY)),
        increasing=dict(marker=dict(color=TARGET_RED)),
        decreasing=dict(marker=dict(color=NEUTRAL_GRAY)),
        totals=dict(marker=dict(color=TARGET_RED)),
    ))

    fig.update_layout(
        title="Target Q2 FY2026 EPS Growth: Headline vs Organic"
              "<br><sub>~80% of reported growth was a one-time tariff refund</sub>",
        yaxis_title="EPS Growth (percentage points)",
        template="plotly_white",
        showlegend=False,
        width=800,
        height=500,
    )

    out_path = OUTPUT_DIR / "bridge2_waterfall.html"
    fig.write_html(out_path)
    print(f"Bridge 2 waterfall written to: {out_path}")


def main():
    data = load_data()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_slope_chart(data["bridge_1_slope_chart"])
    build_waterfall_chart(data["bridge_2_waterfall"])


if __name__ == "__main__":
    main()
