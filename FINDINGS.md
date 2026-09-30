# Tally — findings and deviations, accumulating

Discoveries, corrections, and things that turned out otherwise than the design
assumed. Newest first. Nothing here overrides
[`PREREGISTRATION.md`](PREREGISTRATION.md). Where a finding implies a rule
should change, it is recorded as a **proposed amendment** and stays proposed
until it is numbered under §11.

**F1–F5 were written before any actual CPI figure was joined to the
register. F6 was written after the actuals were assembled but before any
error was computed. It is committed separately so the order can be checked.
F7 is the result. F8 is the brokerage scorecard, which could not be built.**

---

## F8 — There is no public brokerage track record to score

**30 September 2026 · [`data/brokers/`](data/brokers/) · protocol committed
`0f4598c` before any search was run**

The idea that started this project was that brokerages publish CPI
forecasts before every release and that nobody grades them. **The second
half is true because the first half is not.** In the public, free, dated
record, brokerage forecasts are rare.

**What the protocol found, run once as committed:**

| Step | Count |
|---|---|
| Months searched (Jul 2020 – Aug 2026), 3 fixed queries each | 74 |
| Items logged | **1,855** |
| Read: §9 outlet, inflation headline, dated inside the month | **84** articles |
| … by year | 2020: 1 · 2021: 5 · 2022: 7 · 2023: 10 · 2024: 12 · 2025: 25 · 2026: 24 |
| Sentences naming a firm (or "brokerage") with a percentage | 40 |
| **Admitted forecasts naming a firm** | **3** |
| Admitted but unnamed ("the brokerage house") | 1 |

Most of the 40 sentences are about policy rates, fiscal-year averages, core
inflation or month-on-month changes, none of which is the target.

**The admitted forecasts, shown individually, never aggregated:**

| Month | Firm | Forecast | First-release actual | Ministry |
|---|---|---|---|---|
| Sep 2022 | Arif Habib | 25.3% | *not scoreable: first release not archived (F6)* | excluded (directional) |
| Jul 2024 | JS Global | 10.5% | 11.09% | excluded (no number) |
| Mar 2025 | AKD | 0.84% | 0.70% | 1.25% |
| Sep 2025 | *unnamed* | 6.5–7.0% | 5.60% | 4.0% |

### Numbers refused

- **No brokerage accuracy figure, individual or consensus.** §9 needs 24
  admitted months per firm to score a firm alone. The pooled consensus has
  **two scoreable months**. Any average of two errors would be published as a
  finding and read as one.
- **No "brokers beat the Ministry" or "the Ministry beats brokers".** The
  two months above point in opposite directions. Two months settle nothing.

### What a looser rule would add, measured but not applied

The protocol admits a figure only if one sentence names both the firm and the
figure. Profit and Business Recorder usually put the figure in the
**headline** ("inflation expected at 5.75–6.25pc in December 2025: report")
and name the firm elsewhere. Reading headlines would add about **8**
forecasts, **all between December 2024 and December 2025**.

**Not applied.** The protocol was committed before the search. Loosening it
after seeing which articles exist is the move §11 exists to prevent. It would
not change the conclusion either: even with them, no firm comes near 24
months, and no month before December 2024 gains anything.

### What this means for the project

- **The historical brokerage scorecard is not buildable from free public
  sources.** Brokerage CPI previews are client research, and newspapers
  began reporting them regularly only from late 2024.
- **The honest version is prospective.** From now on, record each
  brokerage preview the day it is published, before the release. That is a
  Halflife-style register whose value is that nobody else is keeping it.
  This is recorded as the next step, not started.

---

## F7 — Primary result: the Ministry is no better than a rule anyone could compute

**30 September 2026 · [`results/primary.json`](results/primary.json) ·
pre-registration commit `f6f631e`, register `482d247`, actuals `8ce5ed6`**

| 57 scored months, Jul 2020 – Aug 2026 | Mean abs. error (pp) | RMSE | Mean signed error |
|---|---|---|---|
| **Finance Ministry** | **1.40** | 1.85 | **−0.47** |
| B2 — seasonal rule | 1.32 | 1.80 | −0.16 |
| B1 — no change | 1.80 | — | — |

**Diebold–Mariano (HLN) against B2: 0.67, p = 0.50. Wilcoxon: p = 0.73.**
Under §6 this is reported as written:

> **The official forecast is no better than a rule anyone could compute.**

It does beat B1 ("same as last month"). That is not the comparison §6 names,
and it is not promoted to a headline.

### Why this is stronger than it sounds

F5 established that the Ministry writes in the last days of the target
month, with most of that month's weekly SPI already known. **B2 uses nothing
from the target month at all**: only last month's CPI and five years of
seasonal averages. Four weeks of extra information buy no measurable
accuracy.

### What the Ministry's ranges mean

- **Range hit rate: 32.7%.** A typical Ministry range is one point wide. The
  actual lands inside it about one month in three. No confidence level is
  claimed, so this is a description, not a failed test (§6).
- **The Ministry under-forecasts** (mean error −0.47 pp).
- **The miss is lopsided.** In the 28 months when inflation rose, the mean
  error is **−1.68 pp**; in the 28 months when it fell, **+0.72**. The
  Ministry is slow in both directions and slower on the way up (§7 split,
  descriptive).

### Regimes (§7, descriptive only)

| | n | Ministry MAE | B2 MAE | Range hit rate |
|---|---|---|---|---|
| Actual ≥ 15% | 19 | 2.39 | 2.00 | **11.8%** |
| Actual < 15% | 38 | 0.90 | 0.98 | 42.1% |

The Ministry does slightly better than the rule in calm months and worse in
high-inflation months, which is when a forecast matters most. The primary
test is not re-run within these groups.

### Robustness committed in advance

- **Without the two F4 rows** (PDFs created after month end): n = 55,
  Ministry 1.37 vs B2 1.33, DM p = 0.72. Same verdict.
- **The directional exclusions (F3)** remain unscored. Five of six fall in
  the 2021–22 surge, where the Ministry's scored months are already its
  worst.

### A defect found in the first run, recorded rather than hidden

The first scoring run scored **56** rows, not 57. October 2022 was dropped as
"baseline input missing", because September 2022's YoY was not parsed from
any release (F6). F6, committed before scoring, already said that input would
come from a later statement. The PBS *Historical* table supplied it (23.2%),
and the second run scored all 57.

| Run | n | DM (HLN) | p | Verdict |
|---|---|---|---|---|
| First (row silently dropped) | 56 | 0.49 | 0.62 | no significant difference |
| **Second (reported)** | **57** | **0.67** | **0.50** | **no significant difference** |

Both are shown because the dropped row was discovered only after the first
result was seen.

---

## F6 — How the actuals and baseline inputs were sourced

**30 September 2026 · `data/cpi/` · decisions made before scoring**

**The target (§2).** Each of the 57 targets comes from that month's own PBS
release; none is filled from a later one.

- **36** come from the press release, to two decimals.
- **21** come from the same month's *Monthly Review on Price Indices*,
  because the press release is not archived. The Review is issued alongside
  the release and states the same headline, to one decimal. Most of these 21
  are 2025–26, when the new PBS site stopped posting separate press releases.

§2 names "the monthly PBS press release". Reading the same-month Review as
that release is a judgement, recorded here before any error was computed.
The two sources agree wherever both survive (below).

**Cross-check.** 156 figures are stated in more than one release. **152 agree
to within 0.05.** The four that do not are small later revisions, for example
October 2023 YoY, first 26.89, restated as 26.8. First publication is used
throughout.

**Filenames lie.** PBS's file named "September 2022" is August's release, in
every Wayback capture from November 2022 to June 2026. The month of every
release is read from its text, never its filename. September 2022's own
release is not archived. It is not a target (it is excluded, directional),
but it is B1's input for October 2022. That one input uses the later
statement and is flagged.

**The switch of base.** PBS headlined the 2007-08 base up to July 2019. The
August 2019 release prints both bases and declares 2015-16, so August 2019 is
the first new-base month. The column order in the transition releases
changes (old first in August and September, new first in October); the
parser reads the column by its header.

**B2's seasonal mean (§5)** draws 285 monthly changes:

| Source | Count |
|---|---|
| press release | 155 |
| same-month Review | 55 |
| *Monthly Bulletin of Statistics* table 7.1 (old base, 2015–17) | 35 |
| PBS *Historical Indices* table, computed from one-decimal index levels | 40 |

The last source is a later vintage. §5 allows it, flagged.

**B2's formula.** §5 defines B2 on index levels. It is computed from
published rates with the identity

  YoY_t = (1 + YoY_{t−1}) × (1 + m̄) / (1 + MoM_{t−12}) − 1,

which is algebraically the same forecast. It avoids re-deriving an index
level across the base change. MoM_{t−12} is taken on the new base, since the
YoY it combines with is.

---

## F5 — The Ministry's statements are nowcasts, not forecasts

**30 September 2026 · `data/register/ministry_forecasts.csv`, `pdf_created` column**

The project was pitched as scoring a *forecast of next month*. The PDF
creation dates say otherwise. Of the 57 admitted issues, almost all were
created in the **last week of the month they forecast** (April 2026: 30 April;
June 2024: 28 June; December 2025: 31 December).

So when the Ministry writes its range, it already holds roughly **four of the
month's weekly SPI readings** — about half of the CPI basket, priced across most
of the month. That makes this a **nowcast**: an estimate of a month nearly over.

**What this changes, and what it does not:**

- **The test stands.** B2 uses only last month's CPI, so it has *less*
  information than the Ministry. If the Ministry cannot beat B2 with four weeks
  of prices in hand, that is a stronger finding, not a weaker one.
- **The framing changes.** "The Ministry misses next month's inflation" is the
  wrong sentence. The right one is "the Ministry misses a month that is
  nearly over."
- **It sharpens §10.** Tally's own SPI nowcast is the *like-for-like*
  competitor. B2 is not. That argument should be made in the §10 amendment.

Creation date is metadata. A re-exported PDF gets a new one, so it is
evidence, not proof.

---

## F4 — Two issues may have been written after the answer was public

**30 September 2026 · flag `pdf_created_after_month_end`**

| Issue | Forecast | PDF created | PBS release for that month |
|---|---|---|---|
| August 2023 | 29–31% | **6 September 2023** | early September 2023 |
| February 2024 | 24.5–25.5% | **1 March 2024** | around 1 March 2024 |

§3 dates an issue by what is printed on it; these print only the month, so
both are **admitted under the frozen rule**. That rule was written before
creation dates were seen.

If the Ministry had the outcome when it wrote these, they flatter it.
Exact PBS release dates have not yet been checked.

**Proposed amendment (not applied):** exclude any row whose PDF creation date
falls on or after PBS's release date for the target month. **Whatever the
decision, the primary result will be published both with and without these
rows, side by side.** That commitment is made here, before any error is
known.

---

## F3 — Excluding vague forecasts flatters the Ministry in the months that matter most

**30 September 2026 · `exclusion_reason = directional_only`**

Six issues give only a direction ("slightly less than the last month",
"expected to decelerate"). §3 admits "around last month's level" but not
"below last month's level", so these six are excluded.

**Five of the six fall between October 2021 and September 2022**, the
run-up to the surge, when inflation was hardest to call. The Ministry stopped
giving numbers exactly when numbers were hardest. That is invisible in any
accuracy figure computed on admitted rows only.

**Consequence:** the directional-exclusion count and its dates are reported
next to the primary result, as §3 already requires. It must not be relegated
to a footnote. No rule change is proposed: scoring a direction would require
inventing a number the Ministry never gave.

---

## F2 — Three 2021 issues forecast "next month", and it is unclear which month that is

**30 September 2026 · `exclusion_reason = target_month_ambiguous_next_month`**

February, March and April 2021 give ranges for "next month". Each was
created in the last week of its month, and neighbouring issues forecast
their *own* month. So "next month" could mean either the issue's own month
(its CPI is the next one released) or the following calendar month.

§3 requires the target month to be stated or unambiguous. It is neither, so
all three are excluded. Scoring them either way would mean choosing whichever
reading produced the better or worse number, and that choice would be made
knowing the outcomes.

February 2023 ("28 to 30 percent in coming months") is excluded for the same
reason.

---

## F1 — The weekly SPI files are not deleted; the archiving premise was wrong

**30 September 2026 · feasibility, before pre-registration**

The idea arrived with the claim that PBS overwrites its weekly SPI file and
old weeks return 404. Measured:

- Of the last 52 weekly report files, **38 still download** under their
  dated filenames on the live PBS site. The misses are real gaps, not a
  weekly overwrite.
- The **Wayback Machine holds about 1,570 weekly SPI PDFs** from PBS's old
  site, **2013–2025**. The sampled annex is a clean, text-extractable table:
  51 items, prices by city, minimum/average/maximum.

So the weekly history exists, is public, and anyone can rebuild it. **Tally has
no data moat.** Its claim rests on the pre-registered scoring, not on holding
data others lack.

---

## Extraction record

- **78 issues** listed on finance.gov.pk, March 2020 – August 2026. April 2021
  returned 404 and was recovered from the Wayback Machine (capture
  `20210501030402`). January 2025 is not listed at all.
- **57 admitted, 21 excluded:**
  - no numeric forecast: 9
  - directional only: 6
  - target month ambiguous: 4
  - target is a fiscal-year average: 1
  - text not machine-readable: 1 — April 2023 draws its text as vector shapes
- Four admitted rows carry `month_inferred`: March 2022, October 2022,
  December 2022 and July 2025. For these, the month is given by the
  surrounding paragraph, not the sentence.
- November 2020 states both a point (8.5) and a range (7.6–9.0). §4 takes the
  range midpoint, 8.3. The stated point is recorded in `flags`.
- Every quote, page and hash in the register is found in the PDF by
  [`scripts/build_register.py`](scripts/build_register.py), which fails if
  the typed bounds are not in the quoted sentence.
