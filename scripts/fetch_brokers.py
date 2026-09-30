"""Run the brokerage search protocol once (data/brokers/PROTOCOL.md) and list candidate sentences.

Steps: fixed Google News RSS queries per month -> every item logged -> items from the four
§9 outlets with an inflation title dated inside the month are read -> each page is saved
(gitignored) with its SHA-256 and published timestamp -> sentences naming a brokerage and
a percentage are written out for hand admission. Nothing here decides what is admitted.
"""
import calendar, hashlib, html, json, re, sys, time, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D, RAW = ROOT / "data/brokers", ROOT / "data/raw/brokers"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-US,en;q=0.9"}
OUTLETS = {"brecorder.com": "Business Recorder", "dawn.com": "Dawn",
           "profit.pakistantoday.com.pk": "Profit", "thenews.com.pk": "The News"}
SOURCE_HINT = re.compile(r"Business Recorder|Dawn|Pakistan Today|Profit|The News", re.I)
FIRMS = (r"Topline|Arif Habib|\bAHL\b|JS Global|Insight Securities|Optimus|Pak[- ]Kuwait|PKIC|Ismail Iqbal|\bAKD\b|"
         r"Tresmark|Abbasi and Co|Next Capital|Sherman|Chase Securities|BIPL|Foundation Securities|Intermarket|"
         r"Alpha Capital|Aba Ali Habib|First Capital|Taurus|Pearl Securities|Adam Securities|brokerage")
QUERIES = ["Pakistan inflation {mon} expected", "Pakistan CPI {mon} {y} estimate",
           'Pakistan inflation {mon} Topline OR "Arif Habib" OR AHL OR "JS Global" OR brokerage']


def get(url, data=None, headers=None, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def decode(gn_url):
    """Resolve a news.google.com/rss/articles/... link to the publisher URL."""
    aid = gn_url.split("/articles/")[1].split("?")[0]
    page = get(f"https://news.google.com/rss/articles/{aid}").decode("utf-8", "replace")
    sg = re.search(r'data-n-a-sg="([^"]+)"', page).group(1)
    ts = re.search(r'data-n-a-ts="([^"]+)"', page).group(1)
    inner = json.dumps(["garturlreq", [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
                                       "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0], aid, int(ts), sg])
    body = urllib.parse.urlencode({"f.req": json.dumps([[["Fbv4je", inner, None, "generic"]]])}).encode()
    out = get("https://news.google.com/_/DotsSplashUi/data/batchexecute", body,
              {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}).decode("utf-8", "replace")
    return json.loads(json.loads(out.split("\n\n")[1])[0][2])[1]


def search(q):
    x = get("https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q, "hl": "en-PK", "gl": "PK", "ceid": "PK:en"})).decode("utf-8", "replace")
    items = []
    for it in re.findall(r"<item>(.*?)</item>", x, re.S):
        g = lambda tag: (re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", it, re.S) or [None, ""])[1]
        items.append({"title": html.unescape(g("title")), "source": html.unescape(g("source")),
                      "pubDate": g("pubDate"), "link": g("link")})
    return items


def article(raw):
    t = raw.decode("utf-8", "replace")
    pub = (re.search(r'article:published_time"\s+content="([^"]+)"', t) or re.search(r'"datePublished"\s*:\s*"([^"]+)"', t))
    paras = re.findall(r"<p[^>]*>(.*?)</p>", t, re.S)
    body = " ".join(html.unescape(re.sub(r"<[^>]+>", "", p)) for p in paras)
    return (pub.group(1) if pub else ""), re.sub(r"\s+", " ", body)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    log_path = D / "search_log.jsonl"
    done = set()
    if log_path.exists():  # resumable: a month already logged is never re-queried
        done = {json.loads(l)["month"] for l in open(log_path, encoding="utf-8")}
    m = date(2020, 7, 1)
    with open(log_path, "a", encoding="utf-8") as log:
        while m <= date(2026, 8, 1):
            key = m.strftime("%Y-%m")
            if key not in done:
                last = date(m.year, m.month, calendar.monthrange(m.year, m.month)[1])
                window = f" after:{m.replace(day=15)} before:{last + timedelta(days=2)}"
                for qi, q in enumerate(QUERIES):
                    q = q.format(mon=m.strftime("%B"), y=m.year) + window
                    for it in search(q):
                        log.write(json.dumps({"month": key, "query": qi + 1, "q": q, **it}, ensure_ascii=False) + "\n")
                    time.sleep(2)
                log.flush()
                print("searched", key, flush=True)
            m = (m.replace(day=28) + timedelta(days=4)).replace(day=1)

    log = [json.loads(l) for l in open(log_path, encoding="utf-8")]
    seen, reads, cands = {}, [], []
    url_cache = D / "_decoded.json"
    decoded = json.loads(url_cache.read_text()) if url_cache.exists() else {}
    for it in log:
        month = it["month"]
        y, mo = map(int, month.split("-"))
        pd = time.strptime(it["pubDate"][5:16], "%d %b %Y")
        in_month = (pd.tm_year, pd.tm_mon) == (y, mo)
        if not (SOURCE_HINT.search(it["source"]) and re.search(r"inflation|CPI", it["title"], re.I) and in_month):
            continue
        link = it["link"]
        if link not in decoded:
            try:
                decoded[link] = decode(link)
            except Exception as e:
                decoded[link] = f"DECODE_FAILED: {e}"
            url_cache.write_text(json.dumps(decoded, indent=0))
            time.sleep(1)
        url = decoded[link]
        host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
        if host not in OUTLETS or (url, month) in seen:
            continue
        seen[(url, month)] = True
        name = RAW / (hashlib.sha1(url.encode()).hexdigest() + ".html")
        try:
            raw = name.read_bytes() if name.exists() else get(url)
            name.write_bytes(raw)
        except Exception as e:
            reads.append({"month": month, "url": url, "outlet": OUTLETS[host], "status": f"fetch_failed: {e}"})
            continue
        pub, body = article(raw)
        reads.append({"month": month, "url": url, "outlet": OUTLETS[host], "title": it["title"], "published": pub,
                      "sha256": hashlib.sha256(raw).hexdigest(), "status": "read"})
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", body):
            if re.search(FIRMS, s, re.I) and re.search(r"\d(?:\.\d+)?\s?(?:%|percent|pc)", s):
                cands.append({"month": month, "url": url, "published": pub, "title": it["title"], "sentence": s.strip()})
    for fn, rows in (("reads.jsonl", reads), ("candidates.jsonl", cands)):
        with open(D / fn, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    outlets = {}
    for it in log:
        outlets[it["source"]] = outlets.get(it["source"], 0) + 1
    print(f"{len(log)} logged items, {len(reads)} articles read, {len(cands)} candidate sentences")
    print("top outlets:", sorted(outlets.items(), key=lambda x: -x[1])[:12])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
