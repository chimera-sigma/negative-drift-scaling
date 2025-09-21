# Anti-Dissipative Dynamics — Interactive Demo & Paper

This repository accompanies the workshop paper
**“Anti-Dissipative Dynamics in Neural Network Optimization.”**

It contains:

* **Interactive browser demo** — explore negative drift scaling with SGD, AdamW, and symplectic leapfrog
* **Final paper PDF** — workshop version with results, ablations, and theory
* **Figures & tables** — pre-generated PDFs and LaTeX tables from the paper
* **Scripts** — Python code to regenerate all figures from JSON/CSV outputs

---

##  Quick Start

### Run the Demo

Open directly in a modern browser:

```bash
demo/Anti-Dissipative_Dynamics_Interactive_Demo.html
```

Or serve locally (avoids file:// quirks):

```bash
cd demo
python -m http.server 8000
# Visit http://localhost:8000/Anti-Dissipative_Dynamics_Interactive_Demo.html
```

### Read the Paper

The final workshop PDF is here:
[`paper/Anti_Dissipative_Dynamics_Workshop.pdf`](../paper/Anti_Dissipative_Dynamics_Workshop.pdf)

---

##  Reproducing Figures

Precomputed JSON/CSV summaries are included under `outputs/`.  
The scripts in `scripts/` read these files directly and regenerate the paper figures.

Scripts live in `scripts/`. Outputs are written to `paper/figs/`.

**Fig. 1a — Canonical small-dt band**

```bash
python scripts/make_fig1_overlay_from_audits.py \
  --default  outputs/mem_ablate_precond_band/default/plateau_audit.json \
  --thrash   outputs/mem_ablate_precond_band/thrash/plateau_audit.json \
  --scramble outputs/mem_ablate_precond_band/scramble/plateau_audit.json \
  --out      paper/figs/fig1_lf_precond_small.pdf \
  --style paper --units nats --legend-band "small-dt band" --legend-N 3
```

**Fig. 1b — Wide-dt sweep**

```bash
python scripts/make_fig1_overlay_from_audits.py \
  --default  outputs/lf_precond_canon_precond/default/plateau_audit.json \
  --thrash - --scramble - \
  --out paper/figs/figA1_lf_precond_wide.pdf \
  --style paper --units nats --legend-band "wide-dt sweep"
```

**Fig. 2 — Reversibility**

```bash
python scripts/make_reversibility_plot.py
```

**Fig. 3 — Energy cap engagement**

```bash
python scripts/make_cap_engagement_plot.py
```

---

##  Expected Behavior

* **Canonical band (dt ∈ \[0.002, 0.0035])**: Symplectic slope ≈ −0.08 (95% CI overlaps zero).
* **Outside band (dt ∈ \[0.006, 0.016])**: Symplectic slope strongly positive (\~+2.23).
* **AdamW / SGD**: Always positive slopes in this regime.
* **Diagnostics**:

  * Reversibility shows \~6-order advantage of leapfrog over Euler.
  * Energy-cap engagement ≈ 0% in the canonical band.

---

## Repository Layout

```markdown
demo/    # interactive HTML demo
paper/   # final workshop PDF + generated figures/tables
scripts/ # Python scripts to reproduce figures
outputs/ # JSON/CSV summaries used by scripts
```

---

## Requirements

* **Demo:** Any modern browser (no installs required).
* **Figures:** Python 3.10+, with `matplotlib`, `numpy`, `pandas`.

---

## License

* Code and demo: MIT License
* Paper PDF: CC-BY 4.0

See `LICENSE` for details.

---

