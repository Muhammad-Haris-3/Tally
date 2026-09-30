"""Download every Finance Ministry monthly outlook and list candidate CPI forecast sentences.

Output is for the hand extraction in PREREGISTRATION.md §4, not a result.
PDFs go to data/raw/ (gitignored); their SHA-256 are committed in the manifest so
anyone can check a row against the exact file it was read from.
"""
import csv, hashlib, json, re, sys, unicodedata, urllib.request
from pathlib import Path

import pypdf

BASE = "https://www.finance.gov.pk"
UA = {"User-Agent": "Mozilla/5.0"}
ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data/raw", ROOT / "data/outlooks"
# Must name inflation and look forward; sentences only reporting the past are dropped.
CAND = re.compile(r"(inflation|CPI)", re.I)
FWD = re.compile(r"(expect|project|anticipat|forecast|likely|range|fluctuat|outlook|remain)", re.I)


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    page = get(f"{BASE}/updates.html").decode("utf-8", "replace")
    links = sorted({l for l in re.findall(r'href="(/?economic/[^"]+\.pdf)"', page, re.I)
                    if re.search(r"update|outlook", l, re.I)})
    manifest, cands = [], []
    for link in links:
        url = f"{BASE}/{link.lstrip('/')}"
        name = Path(link).name
        path = RAW / name
        try:
            if not path.exists():
                path.write_bytes(get(url))
            data = path.read_bytes()
            pages = [p.extract_text() or "" for p in pypdf.PdfReader(path).pages]
            status = "ok"
        except Exception as e:  # recorded, not swallowed: a failed issue is a visible gap
            data, pages, status = b"", [], f"error: {e}"
        manifest.append({"file": name, "url": url, "sha256": hashlib.sha256(data).hexdigest() if data else "",
                         "pages": len(pages), "status": status})
        for i, text in enumerate(pages, 1):
            # NFKC: 2022+ issues write "inﬂation" with an fl-ligature, invisible to the regex otherwise.
            flat = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text))
            # Split on sentence ends, but not on the decimal point inside "7.5".
            for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", flat):
                if CAND.search(s) and FWD.search(s) and re.search(r"\d", s):
                    cands.append({"file": name, "page": i, "sentence": s.strip()})
    with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=manifest[0].keys())
        w.writeheader(); w.writerows(manifest)
    with open(OUT / "candidates.jsonl", "w", encoding="utf-8") as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"{len(manifest)} issues, {sum(m['status'] != 'ok' for m in manifest)} failed, {len(cands)} candidate sentences")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
