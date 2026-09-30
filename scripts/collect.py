"""Live collector, run twice daily by .github/workflows/collect.yml. Every output is committed,
so the git history is the timestamped evidence (Amendment 1 §6-7).

  spi      — save each new weekly SPI workbook; merge its 10-week table into spi_weekly.csv
  cpi      — when PBS posts a new Monthly Review, append that month to monthly.csv / spi_monthly.csv
  brokers  — the §9 queries for the current month; every item logged, qualifying articles saved
  nowcast  — on the last day of the month, issue the forecast (nowcast.py live)
Each step is independent: one source being down must not stop the others.
"""
import csv, hashlib, json, re, sys, time, traceback, urllib.parse, zipfile, io
from datetime import datetime, timedelta, timezone, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_brokers as fb  # noqa: E402
import fetch_cpi as fc  # noqa: E402
import build_spi_monthly as bsm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / "data/live"
PBS = "https://www.pbs.gov.pk/wp-content/uploads/2020/07/"
PKT = timezone(timedelta(hours=5))
NOW = datetime.now(timezone.utc)


def get(url):
    return fb.get(url, tries=2)


def spi():
    """Try every day of the last three weeks: PBS's week-ending day moves on holidays."""
    out, found = LIVE / "spi_weekly.csv", []
    rows = {r["week_ending"]: r for r in csv.DictReader(open(out, encoding="utf-8"))} if out.exists() else {}
    for back in range(21):
        d = (NOW.astimezone(PKT) - timedelta(days=back)).date()
        name = f"3.-SPI-Report-{d:%d.%m.%Y}.xlsx"
        dest = LIVE / "spi_files" / name
        if dest.exists():
            continue
        try:
            data = get(PBS + name)
        except Exception:
            continue
        if data[:2] != b"PK":
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        found.append(name)
        for wk, idx in ten_weeks(data):
            if wk not in rows:  # first file to report a week is kept; later restatements ignored
                rows[wk] = {"week_ending": wk, "index": idx, "first_seen_in": name,
                            "first_seen_utc": NOW.isoformat(timespec="seconds")}
    if rows:
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=next(iter(rows.values())).keys())
            w.writeheader(); w.writerows(sorted(rows.values(), key=lambda r: r["week_ending"]))
    return f"{len(found)} new workbook(s): {found}"


def ten_weeks(data):
    """Combined SPI (column F) from the 'last 10 weeks' table of sheet 1."""
    z = zipfile.ZipFile(io.BytesIO(data))
    ss = [re.sub(r"<[^>]+>", "", s) for s in re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode("utf-8"), re.S)]
    x = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    out = []
    for _, body in re.findall(r'<row [^>]*r="(\d+)"[^>]*>(.*?)</row>', x, re.S):
        cells = {c: (ss[int(v)] if 't="s"' in a else v) for c, a, v in
                 re.findall(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(?:<f>.*?</f>)?(?:<v>([^<]*)</v>)?</c>)', body) if v}
        wk = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", cells.get("B", "").strip())
        if wk and re.fullmatch(r"\d+(\.\d+)?", cells.get("F", "")):
            out.append((f"{wk.group(3)}-{wk.group(2)}-{wk.group(1)}", float(cells["F"])))
    return out


def cpi():
    """Append the newest month once its Monthly Review appears. Names vary, so try the known shapes."""
    monthly = list(csv.DictReader(open(ROOT / "data/cpi/monthly.csv", encoding="utf-8")))
    last = monthly[-1]["month"]
    t = fc_shift(last, 1)
    y, m = map(int, t.split("-"))
    mon = date(y, m, 1).strftime("%B")
    for name in (f"Monthly-Review-{mon}-{y}.pdf", f"Monthly-Review-{mon}-{y}-1.pdf",
                 f"Monthly-Review-{mon}-{y}.docx", f"Monthly-Review-{mon}-{y}-1.docx"):
        try:
            data = get(PBS + name)
        except Exception:
            continue
        if data[:4] not in (b"%PDF", b"PK\x03\x04"):
            continue
        text = fc.text_of(data)
        st = {(mo, r): v for mo, r, v in fc.parse_new(text)}
        if (t, "yoy") not in st:
            return f"{name} found but its headline did not parse; nothing appended"
        dest = LIVE / "cpi_files" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        mom = st.get((t, "mom"), "")
        row = {k: "" for k in monthly[0]}
        row.update(month=t, headline_base="2015-16", yoy_first=st[(t, "yoy")], yoy_first_src="review",
                   yoy_later=st[(t, "yoy")], mom_pub=mom, mom_pub_src="review" if mom != "" else "not_found",
                   mom_new=mom, mom_new_src="release" if mom != "" else "not_found")
        with open(ROOT / "data/cpi/monthly.csv", "a", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=monthly[0].keys()).writerow(row)
        spi_rows = {r["month"] for r in csv.DictReader(open(ROOT / "data/cpi/spi_monthly.csv", encoding="utf-8"))}
        own = [(mo, v) for mo, v, ok in bsm.parse(text, t) if mo == t and ok]
        if own and t not in spi_rows:
            with open(ROOT / "data/cpi/spi_monthly.csv", "a", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow([t, own[0][1], 1, 0, "own_review", 0.0])
        return f"appended {t} from {name} (sha256 {hashlib.sha256(data).hexdigest()[:12]})"
    return f"no review yet for {t}"


def fc_shift(m, k):
    y, mo = map(int, m.split("-"))
    i = y * 12 + mo - 1 + k
    return f"{i // 12}-{i % 12 + 1:02d}"


def brokers():
    """PROTOCOL.md queries for the current PKT month; items and articles appended, never rewritten."""
    today = NOW.astimezone(PKT).date()
    m = today.replace(day=1)
    if today.day < 15:  # the protocol window opens on the 15th
        return "window not open (opens on the 15th)"
    key = f"{m:%Y-%m}"
    nxt = (m.replace(day=28) + timedelta(days=4)).replace(day=1)
    window = f" after:{m.replace(day=15)} before:{nxt + timedelta(days=1)}"
    log_path, art_path = LIVE / "brokers/search_log.jsonl", LIVE / "brokers/articles.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    seen = {(j["month"], j["link"]) for j in map(json.loads, open(log_path, encoding="utf-8"))} if log_path.exists() else set()
    new_items = []
    for qi, q in enumerate(fb.QUERIES):
        q = q.format(mon=m.strftime("%B"), y=m.year) + window
        for it in fb.search(q):
            if (key, it["link"]) in seen:
                continue
            seen.add((key, it["link"]))
            rec = {"month": key, "query": qi + 1, "q": q, "first_seen_utc": NOW.isoformat(timespec="seconds"), **it}
            new_items.append(rec)
        time.sleep(2)
    with open(log_path, "a", encoding="utf-8") as fh:
        for rec in new_items:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    saved = 0
    for rec in new_items:
        if not (fb.SOURCE_HINT.search(rec["source"]) and re.search(r"inflation|CPI", rec["title"], re.I)):
            continue
        try:
            url = fb.decode(rec["link"])
        except Exception as e:
            url = f"DECODE_FAILED: {e}"
        host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
        if host not in fb.OUTLETS:
            continue
        snapshot = wayback_save(url)
        try:
            raw, via = get(url), "direct"
        except Exception as e:
            # Dawn and Profit refuse GitHub runners (403, measured 2026-09-30); the Wayback copy
            # was fetched by archive.org's own crawler, so it is read instead.
            try:
                raw, via = get(re.sub(r"/web/(\d+)/", r"/web/\1id_/", snapshot, count=1)), "wayback"
            except Exception:
                with open(art_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"month": key, "url": url, "wayback": snapshot, "status": f"fetch_failed: {e}"}) + "\n")
                continue
        pub, body = fb.article(raw)
        cands = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", body)
                 if re.search(fb.FIRMS, s, re.I) and re.search(r"\d(?:\.\d+)?\s?(?:%|percent|pc)", s)]
        with open(art_path, "a", encoding="utf-8") as fh:
            # Candidate sentences only, never the article: the text belongs to the newspaper. The
            # hash proves which page was read; the URL lets anyone reread it.
            fh.write(json.dumps({"month": key, "url": url, "outlet": fb.OUTLETS[host], "title": rec["title"],
                                 "published": pub, "saved_utc": NOW.isoformat(timespec="seconds"),
                                 "read_via": via, "wayback": snapshot,
                                 "sha256_html": hashlib.sha256(raw).hexdigest(), "candidates": cands,
                                 "status": "saved"}, ensure_ascii=False) + "\n")
        saved += 1
    return f"{len(new_items)} new item(s), {saved} article(s) saved"


def wayback_save(url):
    """Ask the Wayback Machine to capture the page now. Free, keyless, and an independent
    timestamp: evidence the article existed before the release that nobody here can edit."""
    try:
        req = fb.urllib.request.Request("https://web.archive.org/save/" + url,
                                        headers={"User-Agent": "Tally/1.0 (github.com/Muhammad-Haris-3/Tally)"})
        with fb.urllib.request.urlopen(req, timeout=120) as r:
            time.sleep(5)  # anonymous captures are rate-limited; articles arrive a few a day
            return r.geturl() if "/web/" in r.geturl() else ""
    except Exception:
        return ""


def nowcast():
    import nowcast as nc
    nc.live()
    return "checked"


def main():
    LIVE.mkdir(parents=True, exist_ok=True)
    run = {"utc": NOW.isoformat(timespec="seconds")}
    for name, fn in (("spi", spi), ("cpi", cpi), ("brokers", brokers), ("nowcast", nowcast)):
        try:
            run[name] = fn()
        except Exception:
            run[name] = "FAILED: " + traceback.format_exc(limit=2).strip().splitlines()[-1]
    # one line per run: gaps in collection are visible as gaps, and the repo never looks idle
    with open(LIVE / "runs.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(run) + "\n")
    print(json.dumps(run, indent=2))
    if any(str(v).startswith("FAILED") for v in run.values()):
        sys.exit(1)  # a red run on GitHub is the alert (as in Bellwether M8)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
