"""Assemble the monthly CPI table the scoring needs, with the source of every figure.

Inputs, all PBS publications:
  - data/cpi/statements.csv  — figures stated in monthly press releases and reviews (fetch_cpi.py)
  - three Monthly Bulletins of Statistics (Aug 2016, Feb 2017, Dec 2017), table 7.1:
    old-base (2007-08) CPI with the monthly change as published, July 2015 – November 2017
  - "Historical Indices" table: national CPI (2015-16) from July 2017, and the old-base
    series alongside it to August 2019, both to one decimal

Base rule (PREREGISTRATION.md §5): a month's change is taken in the base it was first
published in. PBS headlined the old base to July 2019, and the new base from August 2019
(the August 2019 release prints both and declares 2015-16).
"""
import csv, hashlib, re, sys, urllib.request
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent.parent
D, RAW = ROOT / "data/cpi", ROOT / "data/raw"
NEW_BASE_FROM = "2019-08"
WB = "https://web.archive.org/web/{}id_/{}"
EXTRA = {  # file -> source; Wayback captures pinned so the bytes are reproducible
    "bulletins/monthly_bulletin_of_statistics-august2016.pdf": WB.format("20170510203759", "http://www.pbs.gov.pk/sites/default/files//other/monthly_bulletin/monthly_bulletin_of_statistics-august2016.pdf"),
    "bulletins/monthly_bulletin_of_statistics_feb2017.pdf": WB.format("20181115070859", "http://www.pbs.gov.pk/sites/default/files//other/monthly_bulletin/monthly_bulletin_of_statistics_feb2017.pdf"),
    "bulletins/mbs_dec2017.pdf": WB.format("20181114075945", "http://www.pbs.gov.pk/sites/default/files//Monthly%20Bulletin%20of%20Statistics%20%20December%2C%202017.pdf"),
    "hist.pdf": "https://www.pbs.gov.pk/wp-content/uploads/2020/07/indices_and_growth_rates_historical-1.pdf",
}
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}


def ensure(rel, url):
    p = RAW / rel
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300) as r:
            p.write_bytes(r.read())
    return p


def shift(m, k):
    y, mo = map(int, m.split("-"))
    i = y * 12 + mo - 1 + k
    return f"{i // 12}-{i % 12 + 1:02d}"


def bulletin_mom(path):
    """Table 7.1: '2015 Jul 201.76 0.43 209.53 -0.40' -> {month: CPI MoM}. WPI columns ignored."""
    r = pypdf.PdfReader(path)
    for pg in r.pages[55:65]:
        t = pg.extract_text() or ""
        if "Consumer price index (all urban)" in t:
            break
    out, year = {}, None
    for line in t.splitlines():
        m = re.match(r"\s*(?:(\d{4}) )?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d+\.\d+) (-?\d+\.\d+)", line)
        if m:
            year = int(m.group(1)) if m.group(1) else year
            out[f"{year}-{MON[m.group(2).lower()]:02d}"] = float(m.group(4))
    return out


def historical(path):
    """-> ({month: new-base national index}, {month: old-base index}, {month: national YoY}).

    Pages 1-4 are "Historical Indices"; pages 5-8 are YoY rates in the same row layout.
    Each page is read according to its own heading, so rates are never taken as levels.
    """
    new, old, yoy = {}, {}, {}
    rates = False
    for pg in pypdf.PdfReader(path).pages:
        text = pg.extract_text() or ""
        rates = rates or "Inflation Rate" in text  # the untitled continuation pages inherit
        for line in text.splitlines():
            m = re.match(r"(\d{4}) (\d{1,2}) ((?:-?\d+\.\d+ ?){4,6})$", line.strip())
            if m:
                k = f"{m.group(1)}-{int(m.group(2)):02d}"
                v = [float(x) for x in m.group(3).split()]
                if rates:
                    yoy[k] = v[0]
                else:
                    new[k] = v[0]
                    if len(v) >= 5:
                        old[k] = v[4]
    return new, old, yoy


def main():
    paths = {k: ensure(k, u) for k, u in EXTRA.items()}
    sources = [{"file": k, "url": u, "sha256": hashlib.sha256(paths[k].read_bytes()).hexdigest()} for k, u in EXTRA.items()]

    st = list(csv.DictReader(open(D / "statements.csv", encoding="utf-8")))
    own = {}  # (month, rate) -> (value, kind): the figure stated by that month's OWN release
    later = {}  # (month, rate, base) -> value from any release, for fallbacks
    for s in st:
        if s["revised"] == "1":
            continue
        key = (s["month"], s["rate"])
        if s["stated_in"] == s["month"]:
            # a press release beats the same month's review: the press release is the release
            if key not in own or (s["kind"] == "press_release" and own[key][1] != "press_release"):
                own[key] = (float(s["value"]), s["kind"])
        later.setdefault((s["month"], s["rate"], s["base"]), float(s["value"]))

    bul = {}
    for k in ("bulletins/monthly_bulletin_of_statistics-august2016.pdf", "bulletins/monthly_bulletin_of_statistics_feb2017.pdf", "bulletins/mbs_dec2017.pdf"):
        for m, v in bulletin_mom(paths[k]).items():
            bul.setdefault(m, v)  # earliest bulletin wins: closest to first publication
    hnew, hold, hyoy = historical(paths["hist.pdf"])

    rows = []
    m = "2015-07"
    while m <= "2026-08":
        base = "2015-16" if m >= NEW_BASE_FROM else "2007-08"
        r = {"month": m, "headline_base": base}
        # YoY as first published (the target, §2): own release only, never a later vintage
        if (m, "yoy") in own:
            r["yoy_first"], r["yoy_first_src"] = own[(m, "yoy")][0], own[(m, "yoy")][1]
        else:
            r["yoy_first"], r["yoy_first_src"] = "", "not_found"
        # later vintage, for B1's input only (never the target): a later release, else the table
        r["yoy_later"] = later.get((m, "yoy", "2015-16"), hyoy.get(m, ""))
        # MoM in the base first published in (for the B2 seasonal mean)
        if (m, "mom") in own:
            r["mom_pub"], r["mom_pub_src"] = own[(m, "mom")][0], own[(m, "mom")][1]
        elif base == "2007-08" and m in bul:
            r["mom_pub"], r["mom_pub_src"] = bul[m], "bulletin"
        else:
            idx = hold if base == "2007-08" else hnew
            p = shift(m, -1)
            if m in idx and p in idx:
                r["mom_pub"], r["mom_pub_src"] = round((idx[m] / idx[p] - 1) * 100, 2), "historical_table"
            elif base == "2015-16" and (m, "mom", "2015-16") in later:
                r["mom_pub"], r["mom_pub_src"] = later[(m, "mom", "2015-16")], "later_release"
            else:
                r["mom_pub"], r["mom_pub_src"] = "", "not_found"
        # MoM in the NEW base, any vintage (for the B2 identity's last-year term)
        if (m, "mom", "2015-16") in later:
            r["mom_new"], r["mom_new_src"] = later[(m, "mom", "2015-16")], "release"
        elif m in hnew and shift(m, -1) in hnew:
            r["mom_new"], r["mom_new_src"] = round((hnew[m] / hnew[shift(m, -1)] - 1) * 100, 2), "historical_table"
        else:
            r["mom_new"], r["mom_new_src"] = "", "not_found"
        rows.append(r)
        m = shift(m, 1)

    with open(D / "monthly.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    with open(D / "history_sources.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sources[0].keys())
        w.writeheader(); w.writerows(sources)
    miss = lambda col: [r["month"] for r in rows if r[col] == ""]
    print("yoy_first missing:", miss("yoy_first"))
    print("mom_pub missing:", miss("mom_pub"))
    print("mom_new missing (from 2019-07):", [x for x in miss("mom_new") if x >= "2019-07"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
