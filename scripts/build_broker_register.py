"""Brokerage forecast register (data/brokers/PROTOCOL.md), built like the Ministry register.

Admission is judged by hand in ROWS; the quote, page hash and timestamp are located by script,
which fails if the needle or the typed figure is not in the article. Every candidate sentence
the search produced is either a row here or was rejected for a reason listed in FINDINGS F8.
"""
import csv, hashlib, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_brokers as fb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# (target, firm, lo, hi, status, url, needle)
ROWS = [
    ("2022-09", "Arif Habib (AHL)", 25.3, 25.3, "admitted", "https://www.dawn.com/news/1712344",
     "headline inflation in September is likely to settle at 25.3pc"),
    ("2024-07", "JS Global", 10.5, 10.5, "admitted", "https://www.brecorder.com/news/40313575",
     "July 2024 CPI now further expected to cool down to 10.5%"),
    ("2025-03", "AKD Securities", 0.84, 0.84, "admitted", None,
     "AKD Securities projected inflation to drop to 0.84%"),
    ("2025-09", "(unnamed: 'the brokerage house')", 6.5, 7.0, "unnamed", None,
     "inflation expectations of 6.5-7.0% for September 2025"),
]


def main():
    reads = [json.loads(l) for l in open(ROOT / "data/brokers/reads.jsonl", encoding="utf-8")]
    out, errors = [], []
    for target, firm, lo, hi, status, url, needle in ROWS:
        hits = []
        for r in reads:
            if r["month"] != target or (url and not r["url"].startswith(url)):
                continue
            raw = (fb.RAW / (hashlib.sha1(r["url"].encode()).hexdigest() + ".html")).read_bytes()
            _, body = fb.article(raw)
            i = body.find(needle)
            if i >= 0:
                a = body.rfind(". ", 0, i) + 1
                b = body.find(". ", i + len(needle))
                hits.append((r, body[a:b + 1 if b > 0 else None].strip()))
        if not hits:
            errors.append(f"{target}: needle not found")
            continue
        r, quote = hits[0]
        for x in (lo, hi):
            if not re.search(r"(?<![\d.])" + re.escape(str(x)) + r"(?!\d)", quote):
                errors.append(f"{target}: {x} not in quote")
        out.append({"target_month": target, "firm": firm, "status": status, "lo": lo, "hi": hi,
                    "point": (lo + hi) / 2, "published": r["published"], "outlet": r["outlet"],
                    "url": r["url"], "sha256": r["sha256"], "quote": quote})
    if errors:
        sys.exit("\n".join(errors))
    dest = ROOT / "data/register/broker_forecasts.csv"
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out[0].keys())
        w.writeheader(); w.writerows(out)
    for r in out:
        print(r["target_month"], r["firm"], r["point"], r["published"][:16], "|", r["quote"][:150])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
