"""Monthly SPI month-on-month change, for the Amendment 1 backtest (s_t, backtest definition).

Source: the "SPI inflation ... On MoM basis ..." sentence in PBS's CPI Monthly Reviews, already
downloaded by fetch_cpi.py. Each review states the month, the month before and the same
month a year earlier, so most months are stated three times.

PBS's wording does not always fix the sign: "decreased to 0.3%" is used for a fall of 0.3%
(the next review calls it "a decrease of 0.3%"), "decreased by -0.8%" for a fall of 0.8%,
"(-)0.4%" and "0. 6%" both occur. So each statement is read with an explicit sign where the
words give one, and left unsigned where they do not; a month's value is the value its signed
statements agree on. Months whose statements disagree by more than 0.15 are dropped and
listed, never resolved by hand.
"""
import csv, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_cpi as f  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MONTH = r"(January|February|March|April|May|June|July|August|September|October|November|December),? (\d{4})"
NUM = r"(\(-\)|-)? ?(\d+(?:\. ?\d+)?)"


def signed(word, minus, num, allow_to):
    """-> (value, is_signed). word: increase/decrease/None; minus: '-' or '(-)' or None."""
    v = float(num.replace(" ", ""))
    if minus:
        return -v, True
    if word and word.lower().startswith("increase"):
        return v, True
    if word and word.lower().startswith("decrease"):
        return (-v, True) if not allow_to else (-v, False)
    return v, False  # bare number: probably positive, not trusted alone


def parse(t, file_month):
    m = re.search(r"SPI inflation.{0,160}?On MoM basis,?(.{0,330}?)(?:\d\. )?WPI", t, re.I | re.S)
    if not m:
        return []
    s, out = m.group(1), []
    if re.match(r"\s*no change measured in " + MONTH, s, re.I):
        g = re.match(r"\s*no change measured in " + MONTH, s, re.I)
        out.append((f.ym(g.group(1), g.group(2)), 0.0, True))
    # 2026 forms: "remained stable at 0.7% in June 2026 as compared to the previous month",
    # "remained in negative trajectory i.e. -0.8% in January 2026 & December 2025 each",
    # "... and no change observed in June 2025"
    st = re.search(r"remained stable at " + NUM + r" ?% in " + MONTH + r" as compared to the previous month", s, re.I)
    if st:
        t0 = f.ym(st.group(3), st.group(4))
        out += [(t0, float(st.group(2)), True), (f.prev_month(t0), float(st.group(2)), True)]
    both = re.search(r"(-\d+(?:\.\d+)?) ?% in " + MONTH + r" ?& ?" + MONTH + r" each", s, re.I)
    if both:
        out += [(f.ym(both.group(2), both.group(3)), float(both.group(1)), True),
                (f.ym(both.group(4), both.group(5)), float(both.group(1)), True)]
    nc = re.search(r"no change (?:observed|measured) in " + MONTH, s, re.I)
    if nc:
        out.append((f.ym(nc.group(1), nc.group(2)), 0.0, True))
    named_prev = re.search(r"as compared to (?:an? )?(increase|decrease) of " + NUM + r" ?% in " + MONTH + r" and", s, re.I)
    if named_prev:
        v, ok = signed(named_prev.group(1), named_prev.group(2), named_prev.group(3), allow_to=False)
        out.append((f.ym(named_prev.group(4), named_prev.group(5)), v, ok))
    own = re.search(r"it (increased|decreased)(?: (by|to))? ?" + NUM + r" ?% in " + MONTH, s, re.I)
    if own:
        # "decreased to X" is the ambiguous form; "decreased by X" is signed
        v, ok = signed(own.group(1), own.group(3), own.group(4), allow_to=(own.group(2) or "").lower() == "to")
        out.append((f.ym(own.group(5), own.group(6)), v, ok))
    anchor = own.group(5) + " " + own.group(6) if own else None
    t0 = f.ym(own.group(5), own.group(6)) if own else file_month
    prev = re.search(r"as compared to (?:an? |a )?(?:(increase|decrease|no change)(?: of| in)? )?" + NUM + r"? ?%? ?(?:in )?a month earlier", s, re.I)
    if prev and t0:
        if prev.group(1) and prev.group(1).lower() == "no change":
            out.append((f.prev_month(t0), 0.0, True))
        elif prev.group(3):
            v, ok = signed(prev.group(1), prev.group(2), prev.group(3), allow_to=False)
            out.append((f.prev_month(t0), v, ok))
    ly = re.search(r"and (?:an? )?(?:(in ?crease|de ?crease)(?: of)? )?" + NUM + r" ?% in " + MONTH, s, re.I)
    if ly:
        word = (ly.group(1) or "").replace(" ", "")
        v, ok = signed(word or None, ly.group(2), ly.group(3), allow_to=False)
        out.append((f.ym(ly.group(4), ly.group(5)), v, ok))
    return out


def main():
    stmts = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "data/cpi/releases.csv", encoding="utf-8")):
        if r["revised"] == "1" or not r["sha256"] or r["status"].startswith("unreadable"):
            continue
        name = re.sub(r"[^\w.-]", "_", r["url"].split("/", 3)[3])
        try:
            t = f.text_of((ROOT / "data/raw/cpi" / name).read_bytes())
        except Exception:
            continue
        for month, v, ok in parse(t, r["file_month"]):
            stmts[month].append((v, ok, r["url"].rsplit("/", 1)[1], r["file_month"] == month))
    rows, dropped = [], []
    for month in sorted(stmts):
        sig = [v for v, ok, _, _ in stmts[month] if ok]
        uns = [v for v, ok, _, _ in stmts[month] if not ok]
        own = [v for v, ok, _, is_own in stmts[month] if ok and is_own]
        if own:
            # first publication wins, as for CPI (§2); later restatements are PBS revisions
            rows.append({"month": month, "spi_mom": own[0], "n_signed": len(sig), "n_unsigned": len(uns),
                         "source": "own_review", "max_revision": round(max(abs(v - own[0]) for v in sig), 2)})
            continue
        if sig and max(sig) - min(sig) <= 0.15:
            val = sorted(sig)[len(sig) // 2]
            conflict = [u for u in uns if min(abs(u - val), abs(-u - val)) > 0.15]
            if conflict:
                dropped.append((month, "unsigned statement disagrees", stmts[month]))
                continue
            rows.append({"month": month, "spi_mom": val, "n_signed": len(sig), "n_unsigned": len(uns),
                         "source": "later_reviews", "max_revision": round(max(sig) - min(sig), 2)})
        elif sig:
            dropped.append((month, "signed statements disagree", stmts[month]))
        else:
            dropped.append((month, "no signed statement", stmts[month]))
    with open(ROOT / "data/cpi/spi_monthly.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    with open(ROOT / "data/cpi/spi_monthly_dropped.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["month", "reason", "statements"])
        for d in dropped:
            w.writerow([d[0], d[1], repr(d[2])])
    have = {r["month"] for r in rows}
    need = [f"{y}-{m:02d}" for y in range(2019, 2027) for m in range(1, 13) if "2019-08" <= f"{y}-{m:02d}" <= "2026-08"]
    print(len(rows), "months with a value;", len(dropped), "dropped")
    print("missing 2019-08..2026-08:", [x for x in need if x not in have])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
