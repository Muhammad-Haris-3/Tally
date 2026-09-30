# Tally — pre-registration v1.0 (FROZEN)

**Frozen 30 September 2026**, before any forecast was extracted from any
Finance Ministry document, before any baseline was computed, and before any
error was calculated. Every figure Tally publishes cites the hash of the commit
that froze this file.

---

## 0. What had already been seen

This matters more than usual, because the outcomes are public and I cannot be
blind to them. What the rules below protect is the *comparison*, which has
not been computed.

Seen before writing:

1. **One scored case, from the news:** April 2026, Finance Ministry range 8–9%,
   actual 10.9% (Business Recorder). This case is what prompted the project and
   is a known miss. It is included in the sample like every other month and
   may not be used as a headline example on its own.
2. **Three unscored ranges from search snippets:** November 2025 (5.0–6.0%),
   December 2025 (5.5–6.5%), and the August 2021 wording ("fluctuate around the
   level attained in July"). I have not looked up their outcomes.
3. **General knowledge of Pakistan's CPI path**, including the 2022–23 surge.
   Both the author and the drafter know inflation spiked then. §7 fixes the
   regime split now, so it cannot be chosen after the errors are seen.
4. **Source feasibility:** about 80 Finance Ministry monthly PDFs listed on
   finance.gov.pk, March 2020 to August 2026, and one of them (August 2021)
   extracted as text. PBS weekly SPI history exists live and in the Wayback
   Machine. No SPI file has been parsed.

---

## 1. The question

> **Is the Finance Ministry's published next-release CPI forecast more
> accurate than a rule anyone could compute from last year's prices?**

The null this is built to report: *the official forecast is no better than a
seasonal naive rule.* If the rule wins, that is the finding.

Brokerage forecasts (§9) and Tally's own SPI-driven forecast (§10) are
secondary and are specified separately.

---

## 2. The target

- **Series:** PBS national CPI, year-on-year %, headline, as **first published**
  in the monthly PBS press release. Not later revisions.
- **Why first release:** it is what every forecaster was trying to hit, and
  what the news reported the next day.
- A month whose first release cannot be found is excluded and listed. It is
  never filled from a later vintage.

---

## 3. The sample

**Every Finance Ministry Monthly Economic Update / Outlook issue listed on
finance.gov.pk from the first issue through the August 2026 issue**, plus any
issue recovered from the Wayback Machine.

A forecast row is admitted only if **all** of these hold:

| Condition | Rule |
|---|---|
| Target month is stated or unambiguous from the text | required |
| The issue is dated before PBS's release for that month | required |

**Issue date** is the date printed on the document. If only a month is
printed, it is the first day of that month. If the target month is the same
month the issue is dated, the forecast is admitted: PBS releases a month's CPI
at the start of the following month.
| The forecast is numeric: a range ("8–9%"), a point ("around 7%"), or relative to a stated number ("around July's level") | required |

Every issue produces a row, admitted or not. Excluded rows carry their reason.
**The exclusion count by reason is published beside every result.**

"Around last month's level" is admitted, with the point set to last month's
first-release figure. Hiding a vague forecast in the excluded pile would make
the Ministry look sharper than it is.

---

## 4. Extraction

- The forecast sentence is copied **verbatim** into the register, with the page
  number and the PDF's SHA-256. A reader can check every row without trusting
  me.
- Numbers are taken **only** from that quoted sentence.
- **Point forecast** = midpoint of a range, or the stated point.
- **Relative forecasts** ("around last month's level") are extracted as a
  reference to that month. The number is filled in at scoring time from that
  month's first release — a figure the Ministry already had.
- **An issue with several numeric CPI statements for the target month:** the
  one in the outlook section is used. If there is still more than one, the
  **last** is used. The others are recorded in the row, but not scored.
- **Range width** is recorded as a range's upper limit minus its lower limit;
  a point forecast has width zero.
- Extraction is finished for **all** rows, and the register is committed,
  **before** any actual CPI figure is joined to it. That commit's hash is cited
  in the result.

---

## 5. Baselines, fixed now

Both use only information public before the Ministry's issue date.

- **B1 — no change.** This month's YoY equals last month's first-release YoY.
- **B2 — seasonal naive (primary).** Project this month's CPI index from last
  month's, using the **mean month-on-month change for the same calendar month
  over the previous 5 years**. Then compute YoY against the index 12 months
  earlier. This captures base effects, which drive most of Pakistan's YoY
  swings.
  - **Base change:** PBS rebased the index to 2015–16. Each month-on-month
    change is computed within the base it was published in, so older years use
    the 2007–08 series' own changes. No change is ever computed across the
    month where the two series are linked.
  - Index levels come from PBS's own publications. Where only a later vintage
    of an old index exists, it is used and the row is flagged. This affects the
    baseline only, never the target.

B2 is the primary comparison because it is the baseline the Ministry could most
plausibly be accused of not beating.

---

## 6. Scoring and the primary test

- **Loss:** absolute error of the point forecast, in percentage points.
- **Primary test:** Ministry vs B2, Diebold–Mariano on absolute-error
  differences with the Harvey–Leybourne–Newbold small-sample correction.
  Two-sided, α = 0.05. **Paired Wilcoxon signed-rank** is confirmatory.
- **Reported alongside, always:**
  - MAE and RMSE for the Ministry, B1 and B2;
  - mean signed error (bias). A Ministry that lowballs inflation is a
    different finding from one that is just noisy.
  - **Range hit rate:** the share of actuals inside the stated range. The
    Ministry never claims a confidence level, so this is described, not tested
    against a nominal rate.

### Outcomes, fixed before any error is computed

| Result | Published as |
|---|---|
| Ministry MAE significantly **lower** than B2 | "The official forecast beats the seasonal rule" |
| No significant difference | **"The official forecast is no better than a rule anyone could compute."** |
| Ministry MAE significantly **higher** than B2 | "The official forecast is worse than the seasonal rule" |

Fewer than **40 admitted rows** means the test is not run, and the result is
reported as underpowered, with descriptive figures only.

---

## 7. Secondary splits, declared now

Reported as descriptive results; the primary test is not re-run within them.

- **Regime:** months where the actual YoY ≥ 15%, against months below 15%.
  The line is set now, not chosen after the fact.
- **Direction of surprise:** errors in months where inflation rose compared
  with months where it fell.
- **By format:** range, point, and relative forecasts separately.

---

## 8. What will never be published

- A Ministry accuracy figure computed on a subset chosen after errors were seen.
- One month's miss (including April 2026) presented as representative.
- Any claim about *why* the Ministry misses. Tally measures; it does not
  diagnose.

---

## 9. Brokerages (secondary, specified before collection)

- **Source:** news articles (Business Recorder, Dawn, Profit, The News) that
  quote a named brokerage's forecast for a named month.
- **Admitted only if** the article's timestamp is before the PBS release.
- **Search protocol:** fixed query strings per month, run once, all hits logged.
  This is so coverage gaps are visible rather than filled selectively.
- **Scored per brokerage only if it has ≥ 24 admitted months.** Below that, it
  is pooled into "brokerage consensus" (median of the forecasts admitted for
  that month).
- Same loss and same baselines as §5–6. Brokerages are compared with B2 and with
  the Ministry on **common months only**.

---

## 10. Tally's own forecast (secondary, specified later)

The SPI-driven nowcast is **not specified here**. Its model, features and
backtest window will be fixed in a numbered amendment **before any SPI file is
parsed**. From the freeze of that amendment onward, one forecast per month is
committed to the append-only register before PBS's release.

Stated now, so it cannot be softened later: live forecasts accumulate at 12 a
year, so **a live record under 36 months will be reported as a track record,
not a test.**

---

## 11. Amendments

Any change requires a numbered amendment appended below, recording:

1. what changed, quoting the original text;
2. why;
3. what had already been seen at the time of the change;
4. the commit hash of this file before the change.

A result computed under an amended rule cites the amendment. Any result whose
rule changed after extraction began is published under both rules, side by
side.

### Change log

*(none)*
