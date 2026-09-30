# Brokerage forecasts — collection protocol (PREREGISTRATION.md §9)

**Committed 30 September 2026, before any search in this protocol was run.**
The Ministry result (FINDINGS F7) was known when this was written. That is
why every choice below is mechanical, and why the protocol is run once.

## Months

Every month from **July 2020 to August 2026** (74), matching the Ministry
window, so that comparisons can be made on common months.

## Search, run once

The engine is the Google News RSS endpoint (`news.google.com/rss/search`,
`hl=en-PK`, `gl=PK`, `ceid=PK:en`). It is free and scriptable, and it returns
a dated list that can be logged in full. For each month *M* of year *Y*, the
three queries are fixed, each restricted to `after:{Y-M-15} before:{first
day of M+1, plus one day}`:

1. `Pakistan inflation {Month} expected`
2. `Pakistan CPI {Month} {Y} estimate`
3. `Pakistan inflation {Month} Topline OR "Arif Habib" OR AHL OR "JS Global" OR brokerage`

**Every item returned is logged**, whether or not it is used:
`search_log.jsonl`, with query, title, source, date and Google link. The
coverage this yields is a finding, not a defect to be repaired by searching
harder in the months that come back thin.

## Which articles are read

An item is **read** only if all of the following hold:

- **Outlet:** one of the four §9 names: **Business Recorder, Dawn, Profit
  (Pakistan Today), The News**. Items from other outlets are counted by
  outlet and reported, but not read.
- **Title:** mentions inflation or CPI.
- **Date:** on or before the last day of *M*.

## Which forecasts are admitted

From each read article, the script lists every sentence that:

- names a brokerage from this fixed list: **Topline, Arif Habib / AHL, JS
  Global, Insight Securities, Optimus, Pak-Kuwait / PKIC, Ismail Iqbal, AKD,
  Tresmark, Abbasi and Company, Next Capital, Sherman, Chase Securities, BIPL,
  Foundation Securities, Intermarket, Alpha Capital, Aba Ali Habib, First
  Capital, Taurus, Pearl Securities, Adam Securities**, or says
  "brokerage(s)"; and
- contains a percentage.

A forecast is **admitted** only if its sentence states a YoY CPI figure or
range for month *M*. The month is read from the sentence, or from the
headline where the sentence says "this month". The article's own publication
timestamp (`article:published_time`, else the page's dateline) must fall
**before 00:00 PKT on the first day of M+1**. PBS release times are not
archived, so this is the conservative reading of "before the release".

- Point = the stated figure, or the midpoint of a range.
- Figures attributed to "brokerages" or "analysts" with no firm named go to
  a separate **unnamed** set. They are never merged into a firm's record.
- **One forecast per firm per month:** if a firm appears more than once, the
  latest admitted statement is used.
- **Judgements are typed by hand**, exactly as for the Ministry register. The
  quote, the URL and the SHA-256 of the fetched page are located by script, and
  the script fails if the typed number is not in the quoted sentence.

## Scoring

As in §9: a firm is scored alone only with **≥ 24 admitted months**. Below
that, firms are pooled into a **consensus** (the median of admitted named-firm
forecasts for the month). Same loss and baselines as §5–6. Comparisons with
the Ministry and B2 are made on **common months only**.
