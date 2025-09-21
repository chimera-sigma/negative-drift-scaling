#!/usr/bin/env python3
"""
Make a simple PDF figure for the reversibility demo.

Reads:  outputs/reversibility_demo.json
Writes: paper/figs/fig_reversibility_demo.pdf
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

IN_PATH  = Path("outputs/reversibility_demo.json")
OUT_PATH = Path("paper/figs/fig_reversibility_demo.pdf")

def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing input: {IN_PATH}  (run reversibility_demo.py first)")

    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    k  = data.get("k", "?")
    dt = data.get("dt", "?")

    labels = ["Leapfrog (LF-precond)", "Euler (SGD-like)"]
    vals   = [
        float(data.get("normalized_rt_error_leapfrog", 0.0)),
        float(data.get("normalized_rt_error_euler", 0.0)),
    ]

    # Make sure output dir exists
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Plot (matplotlib, no special styles/colors)
    plt.figure(figsize=(6.0, 4.0), dpi=150)
    bars = plt.bar(labels, vals)
    plt.ylabel("Normalized Round-Trip Error")
    plt.title(f"Reversibility Test (k={k}, dt={dt})")

    # Annotate bars with values
    for b, v in zip(bars, vals):
        plt.text(b.get_x() + b.get_width()/2, b.get_height(),
                 f"{v:.2e}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT_PATH)
    plt.close()
    print(f"Wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
