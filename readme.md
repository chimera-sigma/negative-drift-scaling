# Symplectic Drift Analyzer - README

This repository accompanies the workshop paper on anti-dissipative dynamics in neural optimization.
It ships a single-file browser tool to inspect energy drift and to locate the dt* boundary where the
sign of the mean tail drift flips. The demo replaces the old interactive file.

- New demo: `demo/Symplectic_Drift_Analyzer.html`
- Paper PDF: `paper/Anti_Dissipative_Dynamics_Workshop.pdf`

## What the demo does

- Manual playground - run the leapfrog integrator, add optional noise, and watch H(t) and
  DeltaH(t) = H(t) - H0 in real time.
- dt* boundary finder - scan and bisect a user range of step sizes to find where the sign of the
  mean tail drift flips. Results are aggregated across seeds and logged in a trials table.

The demo is self contained. No builds. No network. One HTML file.

## Quick start

Option A - open directly

- Double click `demo/Symplectic_Drift_Analyzer.html`. Most browsers will run a single-file app
  like this over file:// since it has no module imports, no fetch calls, and no workers.

Option B - serve locally (recommended for all environments)

```bash
cd demo
python -m http.server 8000
# then open
http://localhost:8000/Symplectic_Drift_Analyzer.html
```

VS Code Live Server and `npx http-server -p 8000` work as well.

## How to verify the anti-dissipative pocket

The goal is to confirm a narrow band where drift magnitude decreases as dt increases for the
symplectic update, while first-order methods show the opposite trend in the paper.

A) Manual sanity check

1. Set noise sigma = 0 and click Start. H(t) should stay nearly flat.
2. Choose a mass m near the paper's default, for example m = 0.35.
3. Set noise channel to Gradient and sigma around 0.20 to see stochastic behavior.
4. Click Set E0 = H(t) once after a short warm-up. This zeroes the baseline.
5. Sweep dt by hand. When you are inside the pocket, the tail of DeltaH tends to sit above 0
   (anti-dissipative) for slightly larger dt in that small range, and below 0 outside it.

B) Use the dt* boundary finder

1. Enter a bracket that plausibly straddles the flip. Example: dt lower 0.0022, dt upper 0.0028.
2. Use steps per run 1000 and seeds 20 if the regime is noisy.
3. Click "Find dt* Boundary". The tool scans interior points to form a bracket if needed and
   then bisects until the interval width is below the tolerance.
4. Read the estimate and the trials table. Rows with positive mean tail DeltaH are labeled
   Anti-dissipative. Negative rows are Dissipative.
5. Move the bracket and repeat to map out where the pocket begins and ends for your m and sigma.

C) Match the paper's statistic (optional)

- The paper fits a log-log slope of the tail-median absolute drift across a few dt values. The UI
  reports the sign via the tail mean. If you want the exact figure-of-merit from the paper,
  run several dt values and log the tail-median |DeltaH| per run, then do an OLS fit in a notebook.

## Notes on first-order baselines

- AdamW and SGD show positive drift-size scaling in the referenced experiments. The pocket is a
  symplectic phenomenon and is band specific. See the paper for slopes, bands, and controls.

## Tips

- Re-baseline with Set E0 when you change dt, m, sigma, or noise channel.
- Near dt* use more steps and more seeds.
- If a policy blocks file://, run a local server as in Quick start.

## Repository layout

```
demo/    - Symplectic_Drift_Analyzer.html
paper/   - final workshop PDF and generated figures
scripts/ - Python scripts to reproduce figures from outputs
outputs/ - JSON and CSV summaries for the paper plots
```

## Requirements

- Demo - any modern browser
- Figures - Python 3.10+, numpy, pandas, matplotlib

## License

- Code and demo - MIT
- Paper PDF - CC BY 4.0
