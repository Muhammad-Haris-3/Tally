# Should you plan around the Finance Ministry's inflation forecast?

**Tally — decision memo**
**Date:** 2026-09-30
**Audience:** anyone who reads the Ministry's monthly inflation range and acts
on it: a business setting prices or wages, a saver or investor, a reporter
writing the headline. No technical background assumed.

---

## The short answer

**No. Not on its own.**

Every month, the Finance Ministry's *Economic Update & Outlook* says where
inflation will land: "8–9%", "10–11%". Tally scored every such forecast
from July 2020 to August 2026, 57 months. The scoring rules were written
down and locked in before a single forecast was looked at.

A simple rule does as well: **last month's inflation, plus the change this
month usually brings.** It needs no economists, no models and no inside
information.

| Over 57 months | Average miss |
|---|---|
| Finance Ministry | **1.4 points** |
| The simple rule | **1.3 points** |

The difference is too small to be anything but chance. The Ministry is not
worse than the rule, but it is not better either.

---

## Finding 1: the range is not a range you can rely on

The Ministry's forecast is usually a band one point wide. **The actual
figure lands inside it about one month in three.**

When inflation was high (15% or more, most of 2022–24), it landed inside
**about one month in eight**. The band looks precise, but it is not a promise,
and the Ministry never says how confident it is.

**What this means for you:** treat the band as a centre point. Put roughly
±1.5 points around it before planning. That is closer to how far off it
typically is.

---

## Finding 2: when prices are rising, the Ministry guesses low

In the months when inflation went up, the Ministry's forecast was on average
**1.7 points too low**. When inflation went down, it was about **0.7 points
too high**. It is slow to follow the turn in both directions, and slower on
the way up.

**What this means for you:** if prices have started climbing, the real
number is more likely to come in **above** the Ministry's range than below it.
April 2026 is one example (forecast 8–9%, actual 10.9%), but it is one of 57
months, not proof on its own.

---

## Finding 3: the forecast is made when the month is nearly over

The Ministry's reports are dated in the **last days of the month they
forecast**. By then, most of that month's weekly price data has already been
published. Despite that head start, it does no better than a rule that uses
none of it.

**What this means for you:** the weekly price index (SPI), published every
Friday, is free. Its track record as a forecaster has not been measured
yet (see below). It is the obvious next thing to test.

---

## What this memo cannot tell you

**Whether anyone forecasts better.** Brokerages (Topline, AHL, JS Global and
others) publish their own estimates before each release. Their scorecard is
the next piece of work, and it will be scored by the same locked rules.

**Months when the Ministry gave no number.** Six times it said only "inflation
will ease" or "slightly lower". Five of those were in the 2021–22 surge, the
hardest months to call. They cannot be scored, and their absence makes the
Ministry look slightly **better** than it was.

**Two suspect reports.** Two reports' files were created after the real
figure was already public. Removing them does not change the answer.

---

## What to do

**If you set prices, wages or contracts:** use the Ministry's midpoint only
with a wide margin, and lean high when inflation is rising.

**If you report the number:** "the Ministry expects 8–9%" reads as a
precise estimate. On this record it is a best guess that misses its own
range two times in three.

**If you are the Ministry:** publish how confident the range is meant to be,
and state which weeks of price data it already includes. Both cost nothing,
and they would make the forecast checkable.

---

## Where every figure here comes from

| Claim | Source |
|---|---|
| The 57 forecasts, word for word | `data/register/ministry_forecasts.csv`, each located in its PDF by script |
| Actual inflation | PBS's own first-published monthly releases (`data/cpi/`) |
| Accuracy, ranges, rising vs falling | `results/primary.json`, from `scripts/score.py` |
| The rules, fixed in advance | `PREREGISTRATION.md`, commit `f6f631e` |
| Everything that went differently | `FINDINGS.md` |

Nothing above is quoted from a notebook. Every figure is reproducible from a
committed script.
