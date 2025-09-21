#!/usr/bin/env python3
"""
Make Fig 1 overlay (LF-precond small-dt) from audit/summary JSONs.

Accepts either plateau_audit.json (with "report"/"series": [{dt, tail_median, runs?}, ...])
or slope summary files (with "points": [[dt, tail_median], ...], and optional "n").

Adds guardrails:
- SHA256 short-hash print + duplicate-file warning.
- Duplicate series numeric check.
- Optional in-figure caption with slopeÂ±CI and RÂ².
- Legend context with optional N and band tag.
- Robust minus signs + mathtext sci-notation for log ticks.
- Optional faint fit lines and tiny x-jitter for 'thrash' to reveal overlap.

Usage (plateau audits):
  python scripts/make_fig1_overlay_from_audits.py \
    --default  outputs/mem_ablate_precond_band/default/plateau_audit.json \
    --thrash   outputs/mem_ablate_precond_band/thrash/plateau_audit.json \
    --scramble outputs/mem_ablate_precond_band/scramble/plateau_audit.json \
    --out      paper/figs/fig1_lf_precond_small.pdf \
    --units nats --legend-band "small-dt band" --legend-N 3 --show-fit

Usage (slope summaries):
  python scripts/make_fig1_overlay_from_audits.py \
    --default  outputs/mem_ablate_precond_band/default_slope_summary.json \
    --thrash   outputs/mem_ablate_precond_band/thrash_slope_summary.json \
    --scramble outputs/mem_ablate_precond_band/scramble_slope_summary.json \
    --out      paper/figs/fig1_lf_precond_small.pdf \
    --units nats --legend-band "small-dt band" --legend-N 3 --show-fit
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import matplotlib as mpl
mpl.rcParams["axes.unicode_minus"] = True
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, FixedLocator, LogFormatterMathtext, LogLocator, NullFormatter
import numpy as np


def sha256_short(p: Path, n: int = 10) -> str:
    """Generate short SHA256 hash of file."""
    return hashlib.sha256(p.read_bytes()).hexdigest()[:n]


def _try_get(obj: dict, *keys, default=None):
    """Try to get value from dict using multiple possible keys."""
    for k in keys:
        if k in obj and obj[k] is not None:
            return obj[k]
    return default


def _nice_sparse_log_ticks(ymin, ymax, max_labels=4):
    """Pick 3â€"4 pleasant ticks inside (typically) one decade."""
    if not np.isfinite(ymin) or not np.isfinite(ymax) or ymin <= 0 or ymax <= 0:
        return []
    # Use the decade of ymin (small-dt band stays within one decade)
    k = int(math.floor(math.log10(ymin)))
    base = 10.0 ** k
    mmin, mmax = ymin / base, ymax / base
    # Candidate mantissas every 0.2 from 1.0..9.8, then pick up to max_labels evenly
    cand = np.round(np.arange(1.0, 10.0, 0.2), 1)
    picks = cand[(cand >= mmin - 1e-12) & (cand <= mmax + 1e-12)]
    if picks.size == 0:
        # Fallback to geometric spacing if range is pathological
        picks = np.geomspace(max(1.0, mmin), min(9.99, mmax), num=max_labels)
    idx = np.linspace(0, len(picks) - 1, num=min(max_labels, len(picks)), dtype=int)
    return list((picks[idx] * base).tolist())


def _fmt_mantissa_pow10(y, _pos):
    if not np.isfinite(y) or y <= 0:
        return ""
    k = int(math.floor(math.log10(y)))
    m = y / (10.0 ** k)
    return rf"{m:.1f} Ã— 10$^{{{k}}}$"


def load_series(audit_path: Path) -> Tuple[List[float], List[float], List[int], Optional[int]]:
    """
    Load (dt, tail_median, runs_list, n_points_if_available) from:
      - plateau_audit.json: has "report" or "series" list of dicts with keys {"dt","tail_median","runs" (opt)}
      - *_slope_summary.json: has "points": [[dt, tail_median], ...] and "n"
    Returns (xs, ys, runs, n_points_or_None).
    """
    obj = json.loads(audit_path.read_text(encoding="utf-8"))
    xs, ys, runs = [], [], []

    # Case 1: plateau audit format
    items = _try_get(obj, "report", "series", default=[])
    if isinstance(items, list) and items and isinstance(items[0], dict) and "dt" in items[0]:
        for it in items:
            try:
                x = float(it["dt"])
                y = float(it["tail_median"])
            except Exception:
                continue
            if x > 0 and y > 0:
                xs.append(x)
                ys.append(y)
                runs.append(int(it.get("runs", 0)))
        n_pts = len(xs) if xs else None

    # Case 2: slope summary format
    elif "points" in obj and isinstance(obj["points"], list):
        for pair in obj["points"]:
            if not isinstance(pair, (list, tuple)) or len(pair) < 2:
                continue
            x = float(pair[0])
            y = float(pair[1])
            if x > 0 and y > 0:
                xs.append(x)
                ys.append(y)
        # no per-dt run counts here
        runs = [0] * len(xs)
        n_pts = int(obj.get("n", len(xs))) if xs else None
    else:
        n_pts = None

    # sort by dt
    z = sorted(zip(xs, ys, runs), key=lambda t: t[0])
    xs = [x for x, _, _ in z]
    ys = [y for _, y, _ in z]
    runs = [r for _, _, r in z]
    return xs, ys, runs, n_pts


def ols_log10(xs: List[float], ys: List[float]) -> Optional[Dict[str, float]]:
    """
    OLS of log10(y) ~ m * log10(x) + b with a simple 95% CI for m and R^2.
    Requires >= 3 points.
    """
    pts = [(x, y) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(pts) < 3:
        return None
    lx = [math.log10(x) for x, _ in pts]
    ly = [math.log10(y) for _, y in pts]
    n = len(lx)
    xm = sum(lx) / n
    ym = sum(ly) / n
    sxx = sum((x - xm) ** 2 for x in lx)
    if sxx == 0:
        return None
    sxy = sum((x - xm) * (y - ym) for x, y in zip(lx, ly))
    m = sxy / sxx
    b = ym - m * xm
    rss = sum((y - (m * x + b)) ** 2 for x, y in zip(lx, ly))
    tss = sum((y - ym) ** 2 for y in ly)
    r2 = 0.0 if tss == 0 else 1 - rss / tss
    df = n - 2
    s2 = rss / max(1, df)
    se = math.sqrt(s2 / sxx) if sxx > 0 else float("inf")

    # crude t criticals (95% two-tailed). Good enough for small n.
    if df <= 0:
        tcrit = 1.96
    elif df == 1:
        tcrit = 12.706
    elif df == 2:
        tcrit = 4.303
    elif df <= 20:
        tcrit = 2.086
    else:
        tcrit = 1.96

    lo, hi = m - tcrit * se, m + tcrit * se
    return {"m": m, "b": b, "lo": lo, "hi": hi, "r2": r2, "n": n}


def fmt_small_dt(x: float, _pos: int) -> str:
    """Format small dt values for axis ticks."""
    return f"{x:.4f}".rstrip("0").rstrip(".")


def nearly_identical(a: List[float], b: List[float], tol: float = 1e-12) -> bool:
    """Check if two series are numerically identical within tolerance."""
    if len(a) != len(b):
        return False
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def make_overlay(
    p_default: Path,
    p_thrash: Optional[Path],
    p_scramble: Optional[Path],
    out_path: Path,
    show_fit: bool = False,
    y_units: Optional[str] = None,
    legend_band: Optional[str] = None,
    legend_N: Optional[int] = None,
    caption_in_figure: bool = True,
    thrash_jitter_pct: float = 0.0,
    style: str = "overlay",
) -> None:
    """Create overlay plot from audit files."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    specs = []
    specs.append(("LF-default", p_default, "#2563eb", "o", "-"))
    if p_thrash is not None:
        specs.append(("LF-thrash", p_thrash, "#16a34a", "s", "-"))
    if p_scramble is not None:
        specs.append(("LF-scramble", p_scramble, "#a855f7", ">", "--"))

    # Hash prints + duplicate-file warning
    print("[INFO] input hashes (sha256[:10]):")
    digests = []
    for lbl, p, *_ in specs:
        d = sha256_short(p)
        digests.append((lbl, d))
        print(f"    {lbl:11s} {d}  {p}")
    buckets = {}
    for lbl, d in digests:
        buckets.setdefault(d, []).append(lbl)
    dups = [lab for lab in buckets.values() if len(lab) > 1]
    if dups:
        print("[WARN] Two or more inputs are byte-identical:", dups)

    # Figure style
    plt.rcParams["font.size"] = 10
    fig = plt.figure(figsize=(6.6, 4.4), dpi=200)
    ax = plt.gca()
    ax.set_xscale("log")
    ax.set_yscale("log")

    dt_all = set()
    handles, labels, caption = [], [], []
    series_data = {}  # label -> (xs, ys)

    for label, path, color, marker, lstyle in specs:
        xs, ys, runs, _n_pts = load_series(path)
        if label.lower().endswith("thrash") and thrash_jitter_pct:
            xs = [x * (1.0 + thrash_jitter_pct / 100.0) for x in xs]

        series_data[label] = (xs, ys)
        dt_all.update(xs)

        if not xs:
            continue

        # line then markers
        ax.loglog(xs, ys, color=color, linestyle=lstyle, linewidth=2.1, alpha=1.0, zorder=2)
        ax.loglog(xs, ys, color=color, linestyle="None", marker=marker,
                  markersize=6, markerfacecolor="white", markeredgecolor=color,
                  markeredgewidth=1.2, zorder=3)

        fit = ols_log10(xs, ys)
        leg_text = label
        if fit:
            m, lo, hi, r2 = fit["m"], fit["lo"], fit["hi"], fit["r2"]
            if r2 < 0.30 and "scramble" in label.lower():
                # FIXED: Use mathtext to avoid encoding issues in PDF backends
                leg_text = rf"{label} (low $R^2$)"
            if show_fit:
                x0, x1 = min(xs), max(xs)
                xx = [x0, x1]
                yy = [10 ** (m * math.log10(x) + fit["b"]) for x in xx]
                ax.loglog(xx, yy, color=color, alpha=0.18, linewidth=1.2, zorder=1)
            caption.append(f"{label}: m={m:+.3f} [{lo:+.3f},{hi:+.3f}] R^2={r2:.2f}")
        else:
            caption.append(f"{label}: fit n/a")

        handles.append(Line2D([0], [0], color=color, marker=marker, linestyle=lstyle,
                              markersize=6, markerfacecolor="white", markeredgecolor=color,
                              markeredgewidth=1.2, linewidth=2.1))
        labels.append(leg_text)

    # numeric duplicate warning
    keys = list(series_data.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            xa, ya = series_data[a]
            xb, yb = series_data[b]
            if xa and xb and nearly_identical(xa, xb) and nearly_identical(ya, yb):
                print(f"[WARN] Series '{a}' and '{b}' appear numerically identical.")

    # Tick policy toggled by style
    style = (style or "overlay").lower()
    if style == "overlay":
        # Sparse y majors; remove minor labels to avoid scrunch
        ymin, ymax = ax.get_ylim()
        yticks = _nice_sparse_log_ticks(ymin, ymax, max_labels=4)
        if yticks:
            ax.yaxis.set_major_locator(FixedLocator(yticks))
            ax.yaxis.set_major_formatter(FuncFormatter(_fmt_mantissa_pow10))
        ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=()))
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.margins(y=0.08)
    else:
        # paper style: let Matplotlib choose (denser labels, sci-notation)
        pass

    # labels/ticks
    ax.set_xlabel(r"Step size $dt$ (log)")
    y_label = (r"Tail median $|\Delta H|$ (log)"
               if not y_units
               else rf"Tail median $|\Delta H|$ ({y_units}, log)")
    ax.set_ylabel(y_label)
    if style == "overlay":
        if dt_all:
            ticks = sorted(set(round(d, 4) for d in dt_all))
            ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FuncFormatter(fmt_small_dt))
    else:
        # paper style: leave formatter/locator to Matplotlib (shows 2Ã—10â»Â³, 3Ã—10â»Â³, â€¦)
        pass
    ax.grid(True, which="both", linestyle="--", alpha=0.35)

    # legend
    if legend_band and legend_N:
        legend_title = f"Ablation (N={legend_N}; {legend_band})"
    elif legend_band:
        legend_title = f"Ablation ({legend_band})"
    elif legend_N:
        legend_title = f"Ablation (N={legend_N})"
    else:
        legend_title = "Ablation"
    if style == "paper":
        legend_title = None
    ax.legend(handles, labels, title=legend_title, fontsize=9, title_fontsize=10, loc="best")

    if caption_in_figure and (style != "paper") and caption:
        ax.text(0.02, 0.98, "\n".join(caption),
                transform=ax.transAxes, ha="left", va="top",
                fontsize=8, alpha=0.90,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.75),
                zorder=4)

    fig.tight_layout()
    fig.savefig(out_path, transparent=True, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"[OK] wrote: {out_path}")
    print("[Caption Suggestion]")
    print("; ".join(caption))


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--default", required=True, help="path to default plateau_audit.json OR slope_summary.json")
    ap.add_argument("--thrash", default=None, help="optional path; use '-' to skip")
    ap.add_argument("--scramble", default=None, help="optional path; use '-' to skip")
    ap.add_argument("--out", default="paper/figs/fig1_lf_precond_small.pdf", help="output PDF path")
    ap.add_argument("--show-fit", action="store_true", help="draw faint trend lines")
    ap.add_argument("--units", default=None, help="y-axis units label, e.g. 'nats' or 'bits'")
    ap.add_argument("--legend-band", default=None, help="context note for legend title, e.g., 'small-dt band'")
    ap.add_argument("--legend-N", type=int, default=None, help="seed count per dt to include in legend title")
    ap.add_argument("--no-figure-caption", action="store_true", help="disable on-figure caption text")
    ap.add_argument("--style", choices=["overlay","paper"], default="overlay",
                    help="overlay: sparse y & explicit dt ticks; paper: auto ticks, no legend title, no caption")
    ap.add_argument("--thrash-jitter", type=float, default=0.0,
                    help="percent x-jitter to apply to 'thrash' markers (e.g., 1.5)")
    return ap.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    def norm(p):
        if p is None:
            return None
        ps = str(p).strip()
        if ps in {"-", "", "none", "NONE"}:
            return None
        return Path(ps)
    
    make_overlay(
        p_default=Path(args.default),
        p_thrash=norm(args.thrash),
        p_scramble=norm(args.scramble),
        out_path=Path(args.out),
        show_fit=args.show_fit,
        y_units=args.units,
        legend_band=args.legend_band,
        legend_N=args.legend_N,
        caption_in_figure=(not args.no_figure_caption) and (args.style != "paper"),
        thrash_jitter_pct=args.thrash_jitter,
        style=args.style,
    )


if __name__ == "__main__":
    main()