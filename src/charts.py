"""
charts.py — render the two PDF charts from outputs/metrics.json.

Chart 1: Paytm share by occasion (count vs value).
Chart 2: barrier codes (from the coding sheet's final_code column).

Charts render from computed metrics / confirmed codes only — never invented data.
"""
from __future__ import annotations

import os
import sys
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from ingest import load_config  # noqa: E402

PAYTM_BLUE = "#00BAF2"
ACCENT = "#002970"


def chart1_share_by_occasion(metrics: dict, out_path: str) -> str:
    by_occ = metrics.get("paytm_share_by_occasion", {})
    occasions = [o for o in by_occ if o and o.lower() != "nan"]
    if not occasions:
        return _placeholder(out_path, "Chart 1 — no payment data yet")
    counts = [(by_occ[o]["all"]["by_count"] or 0) * 100 for o in occasions]
    values = [(by_occ[o]["all"]["by_value"] or 0) * 100 for o in occasions]

    x = range(len(occasions))
    w = 0.38
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([i - w / 2 for i in x], counts, w, label="By count", color=PAYTM_BLUE)
    ax.bar([i + w / 2 for i in x], values, w, label="By value (₹)", color=ACCENT)
    ax.set_xticks(list(x))
    ax.set_xticklabels(occasions, rotation=20, ha="right")
    ax.set_ylabel("Paytm share (%)")
    ax.set_title("Chart 1 — Paytm share by occasion (count vs value)")
    ax.legend()
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def chart2_barrier_codes(coding_csv: str, out_path: str) -> str:
    if not os.path.exists(coding_csv):
        return _placeholder(out_path, "Chart 2 — barrier codes (awaiting final_code)")
    df = pd.read_csv(coding_csv)
    if "final_code" not in df.columns:
        return _placeholder(out_path, "Chart 2 — no final_code column yet")
    codes = df["final_code"].dropna().astype(str).str.strip()
    codes = codes[codes != ""]
    if codes.empty:
        return _placeholder(out_path, "Chart 2 — final_code not filled yet")
    vc = codes.value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(vc.index, vc.values, color=PAYTM_BLUE)
    ax.set_xlabel("Respondents")
    ax.set_title("Chart 2 — Unprompted barriers to using Paytm")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def _placeholder(out_path: str, msg: str) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.text(0.5, 0.5, msg, ha="center", va="center", wrap=True)
    ax.axis("off")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def render_all(metrics: dict, charts_dir: str, coding_csv: str) -> dict:
    os.makedirs(charts_dir, exist_ok=True)
    return {
        "chart1": chart1_share_by_occasion(metrics, os.path.join(charts_dir, "chart1_share_by_occasion.png")),
        "chart2": chart2_barrier_codes(coding_csv, os.path.join(charts_dir, "chart2_barrier_codes.png")),
    }


def main():
    cfg = load_config()
    paths = cfg["paths"]
    metrics_path = os.path.join(ROOT, paths["metrics"])
    if not os.path.exists(metrics_path):
        print(f"NOTE: {metrics_path} not found — run src/analyze.py first.")
        return
    with open(metrics_path, encoding="utf-8") as fh:
        metrics = json.load(fh)
    out = render_all(metrics, os.path.join(ROOT, paths["charts_dir"]),
                     os.path.join(ROOT, paths["coding_sheet"]))
    for k, v in out.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    sys.exit(main())
