"""Collect PBS's monthly CPI releases and read the headline rates each one published.

Target (PREREGISTRATION.md §2): national CPI YoY as FIRST published. So each file is
fetched from its EARLIEST Wayback capture, which is the copy closest to publication;
a later "Revised" re-upload of the same month is recorded but never preferred.

Two release formats:
  - base 2015-16 (from mid-2019): states YoY and MoM for the month, the previous month
    and the same month a year earlier, in one "CPI inflation General" paragraph.
  - base 2007-08 press releases (to mid-2019): state the month's MoM and YoY only.
Output: data/cpi/releases.csv, one row per file, and data/cpi/statements.csv, one row per
(source, month, rate) figure a file states — so a month's figure can be traced to the
release that first published it, as opposed to a later one that restated it.
"""
import csv, hashlib, io, json, re, sys, time, unicodedata, urllib.request, zipfile
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/cpi"
RAW = ROOT / "data/raw/cpi"
UA = {"User-Agent": "Mozilla/5.0"}
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
MONTH_RE = r"(January|February|March|April|May|June|July|August|September|October|November|December)[, ]*(\d{4})"
MON_ABBR = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?[, ]*(\d{4})"


def month_of_name(url):
    n = url.rsplit("/", 1)[1].lower().replace("%20", " ").replace("%2c", ",").replace("febuary", "february")
    m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[ ,_.-]*(\d{4}|\d{2})(?!\d)", n)
    if not m:
        return None
    y = int(m.group(2))
    return f"{y + 2000 if y < 100 else y}-{MON[m.group(1)]:02d}"


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read(), r.geturl()


def fetch(url):
    """Earliest Wayback capture first; the live file only if nothing was archived."""
    for src in (f"https://web.archive.org/web/1996id_/{url}", url):
        for attempt in range(3):
            try:
                data, final = get(src)
                if data[:4] in (b"%PDF", b"PK\x03\x04"):
                    return data, final
                break
            except Exception:
                time.sleep(3 * (attempt + 1))
    return None, None


def text_of(data):
    if data[:4] == b"PK\x03\x04":  # docx
        xml = zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml").decode("utf-8", "replace")
        t = re.sub(r"</w:p>", "\n", xml)
        t = re.sub(r"<[^>]+>", "", t)
    else:
        t = "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(io.BytesIO(data)).pages[:6])
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"(?<=[a-z]) -(?=[a-z])", "-", t)  # "year -on-year" -> "year-on-year"
    return re.sub(r"\s+", " ", t)


def ym(mon, yr):
    return f"{int(yr)}-{MON[mon[:3].lower()]:02d}"


N = r"(\d+(?:\.\d+)?)"
CMP = r"(?:an? (increase|decrease) of )?" + N + r" ?%"  # "an increase of 8.6%", or bare "5.6%"


def verb_value(verb, prep, v, rate):
    """Sign a stated figure, or None where PBS's wording does not fix the sign.

    "increased by/to X" -> +X. "decreased by X" -> -X. "decreased to X" is a LEVEL for YoY
    (inflation fell to X%, still positive) but ambiguous for MoM, where PBS uses it for both
    a negative change and a smaller positive one — so it is not read at all.
    """
    if verb.lower().startswith("increase"):
        return v
    if prep == "by":
        return -v
    return v if rate == "yoy" else None


def parse_new(t):
    """Review 'CPI inflation General' paragraph -> list of (month, rate, value).

    Wording varies across years: "increased by" / "increased to", "as compared to an increase
    of 8.6% in the previous month" / "as compared to 5.6% of the previous month". Each figure
    is matched on its own so one unfamiliar clause cannot lose the others.
    """
    m = re.search(r"CPI inflation General ?,?(.{0,800}?)(?:\d\. )?CPI inflation Urban", t, re.I)
    if not m:
        return []
    p, out = m.group(1), []
    y = re.search(r"(increased|decreased) (by|to) " + N + r" ?% on year-on-year basis in " + MONTH_RE, p, re.I)
    if y:
        t0 = ym(y.group(4), y.group(5))
        v = verb_value(y.group(1), y.group(2).lower(), float(y.group(3)), "yoy")
        out.append((t0, "yoy", v))
        rest = p[y.end():]
        a = re.match(r" as compared to " + CMP + r" (?:in|of) the previous month,? and " + CMP + r" in " + MONTH_RE, rest, re.I)
        if a and a.group(1) != "decrease" and a.group(3) != "decrease":  # a negative YoY would be a first
            out += [(prev_month(t0), "yoy", float(a.group(2))), (ym(a.group(5), a.group(6)), "yoy", float(a.group(4)))]
    mo = re.search(r"month-on-month basis,? it (increased|decreased) (by|to) " + N + r" ?% in " + MONTH_RE, p, re.I)
    if mo:
        t0 = ym(mo.group(4), mo.group(5))
        v = verb_value(mo.group(1), mo.group(2).lower(), float(mo.group(3)), "mom")
        if v is not None:
            out.append((t0, "mom", v))
        a = re.match(r" as compared to " + CMP + r" in the previous month,? and " + CMP + r" in " + MONTH_RE, p[mo.end():], re.I)
        if a:
            sg = lambda w: -1 if w == "decrease" else 1
            out += [(prev_month(t0), "mom", sg(a.group(1)) * float(a.group(2))),
                    (ym(a.group(5), a.group(6)), "mom", sg(a.group(3)) * float(a.group(4)))]
    return [s for s in out if s[2] is not None]


def parse_press(t):
    """Press-release summary table, both bases -> [(month, rate, value)] for its own month.

    The month is read from "Inflation Rate, October, 2020 over ...", never from the title:
    the October 2020 release is headed "FOR THE MONTH OF SEPTEMBER, 2020".
    August–October 2019 print both bases in two columns, in an order that changes between
    releases ("2007-08 2015-16" in August, "2015-16 2007-08" in October). The titles declare
    base 2015-16, so the 2015-16 column is the headline, located by its header. Returns
    (statements, base).
    """
    num = r"(-? ?\d+(?:\.\d+)?)"  # June 2023 prints "- 0.26"
    head = r"Inflation Rate,? " + MON_ABBR + r",? over [A-Za-z]+,? ?\d{4} "
    # Not "\s*%?" before the optional column: \s* would eat the space it needs.
    second = r"(?:\s?%)?(?:\s+" + num + r"(?![\d,]))?"
    mom = re.search(head + r"\((?:Previous month|Month on Month)\) ?" + num + second, t, re.I)
    yoy = re.search(head + r"\((?:Corresponding month|Year on Year)\) ?" + num + second, t, re.I)
    if not (mom and yoy):
        return [], ""
    cols = re.search(r"(2007-08|2015-16) (2007-08|2015-16) Inflation Rate", t)
    two_cols = mom.group(4) is not None and cols
    base = "2015-16" if (two_cols or re.search(r"Base (Year )?2015-16", t, re.I)) else "2007-08"
    g = (4 if cols.group(2) == "2015-16" else 3) if two_cols else 3
    pick = lambda m: float(m.group(g).replace(" ", ""))
    return [(ym(mom.group(1), mom.group(2)), "mom", pick(mom)),
            (ym(yoy.group(1), yoy.group(2)), "yoy", pick(yoy))], base


def prev_month(s):
    y, m = map(int, s.split("-"))
    return f"{y - (m == 1)}-{(m - 2) % 12 + 1:02d}"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    urls = [u.strip() for u in open(D / "candidate_urls.txt") if u.strip()]
    releases, statements = [], []
    for u in urls:
        month = month_of_name(u)
        name = re.sub(r"[^\w.-]", "_", u.split("/", 3)[3])
        path = RAW / name
        final = ""
        if path.exists():
            data = path.read_bytes()
            final = json.loads((RAW / (name + ".src")).read_text()) if (RAW / (name + ".src")).exists() else ""
        elif (RAW / (name + ".fail")).exists():  # delete the marker to retry
            data = None
        else:
            data, final = fetch(u)
            if data:
                path.write_bytes(data)
                (RAW / (name + ".src")).write_text(json.dumps(final))
            else:
                (RAW / (name + ".fail")).write_text("")
        row = {"file_month": month or "", "url": u, "fetched_from": final or "", "sha256": "",
               "base": "", "kind": "", "revised": int(bool(re.search(r"revis", u, re.I))), "status": ""}
        if not data:
            row["status"] = "not_retrievable"
            releases.append(row)
            continue
        row["sha256"] = hashlib.sha256(data).hexdigest()
        try:
            t = text_of(data)
        except Exception as e:
            row["status"] = f"unreadable: {e}"
            releases.append(row)
            continue
        st, row["base"] = parse_press(t)
        row["kind"] = "press_release" if st else ""
        if not st:
            st = parse_new(t)
            row["base"], row["kind"] = ("2015-16", "review") if st else ("", "")
        row["status"] = "parsed" if st else "no_headline_found"
        releases.append(row)
        for mo, rate, v in st:
            # A press release states only its own month, so that is the release's month —
            # filenames are not trusted (the "September 2022" file is August's release).
            own = st[0][0] if row["kind"] == "press_release" else (month or "")
            statements.append({"month": mo, "rate": rate, "value": v, "stated_in": own,
                               "kind": row["kind"], "base": row["base"], "revised": row["revised"],
                               "url": u, "sha256": row["sha256"]})
        print(f"{row['status']:>18} {month} {u.rsplit('/', 1)[1]}", flush=True)
    for fn, rows in (("releases.csv", releases), ("statements.csv", statements)):
        with open(D / fn, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader(); w.writerows(rows)
    print(f"{len(releases)} files, {sum(r['status'] == 'parsed' for r in releases)} parsed, {len(statements)} statements")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
