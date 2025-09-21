#!/usr/bin/env python3
"""
Make a PDF figure for the cap engagement analysis.

Reads:  outputs/cap_vs_dt.csv
Writes: paper/figs/fig_cap_engagement_small.pdf
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

IN_PATH  = Path("outputs/cap_vs_dt.csv")
OUT_PATH = Path("paper/figs/fig_cap_engagement_small.pdf")

def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing input: {IN_PATH}")

    df = pd.read_csv(IN_PATH).sort_values("dt")

    # Expected columns: dt, fraction_capped_mean, fraction_capped_ci95_low, fraction_capped_ci95_high
    if "fraction_capped_mean" not in df.columns:
        raise ValueError(f"CSV missing expected column 'fraction_capped_mean'. Found: {list(df.columns)}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 4), dpi=150)

    # Plot mean with error bars
    plt.errorbar(
        df["dt"], df["fraction_capped_mean"],
        yerr=[df["fraction_capped_mean"] - df["fraction_capped_ci95_low"],
              df["fraction_capped_ci95_high"] - df["fraction_capped_mean"]],
        fmt="o-", capsize=4, color="tab:blue", label="Cap engagement"
    )

    plt.xlabel(r"Step size $dt$")
    plt.ylabel("Cap engagement fraction")
    plt.title("Energy Cap Engagement vs Step Size")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_PATH)
    plt.close()
    print(f"Wrote {OUT_PATH}")

if __name__ == "__main__":
    main()