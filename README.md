# Tally

**Pakistan's Finance Ministry publishes a CPI inflation forecast every month.
Nobody keeps score. Tally does.**

## Result (pre-registered, 57 months, July 2020 – August 2026)

> **The Ministry's forecast is no better than a rule anyone could compute
> from last year's prices.**

| | Mean absolute error |
|---|---|
| Finance Ministry | 1.40 points |
| Seasonal rule (last month + usual change for this month) | 1.32 points |

Diebold–Mariano p = 0.50. The actual figure lands inside the Ministry's
stated range **one month in three**, and about one month in eight when inflation is
above 15%.

The Ministry writes each forecast in the **last days of the month it
forecasts**, with most of that month's weekly price data already in hand. The
rule uses none of it.

## Why the record can be trusted

| Commit | What was fixed, before what was seen |
|---|---|
| `f6f631e` | [Pre-registration](PREREGISTRATION.md): target, baselines, test, verdict wording — before any forecast was extracted |
| `482d247` | [Forecast register](data/register/ministry_forecasts.csv): 78 issues, each quote located in its PDF by script — before any actual CPI was joined |
| `8ce5ed6` | Actual CPI from PBS's first-published releases, and every sourcing judgement — before any error was computed |

Everything that went differently from the plan is in
[FINDINGS.md](FINDINGS.md). That includes a row the first scoring run
silently dropped.

## Honest limits

- **One forecaster so far.** Brokerage forecasts (§9) are not yet collected.
- **The Ministry often gives no number** when inflation is hardest to call.
  Six directional-only months, five of them in the 2021–22 surge, cannot be
  scored (FINDINGS F3).
- **Two issues' PDFs postdate their month.** The result holds without them
  (FINDINGS F4).
- **No data moat.** Every source is public and archived (FINDINGS F1). What
  Tally adds is the pre-committed scoring.

## Reproduce

```bash
pip install pypdf numpy scipy
python scripts/fetch_outlooks.py && python scripts/build_register.py
python scripts/fetch_cpi.py && python scripts/build_cpi.py
python scripts/score.py
```
