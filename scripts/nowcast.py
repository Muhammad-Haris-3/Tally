"""Tally's SPI nowcast (PREREGISTRATION.md Amendment 1).

    m_hat_t = a_t + b_t * s_t        OLS of new-base CPI MoM on SPI MoM, Aug 2019 .. t-1, expanding
    YoY_t   = (1 + YoY_{t-1}) * (1 + m_hat_t) / (1 + MoM_{t-12}) - 1     (B2's identity)

`python scripts/nowcast.py backtest` scores it on the Ministry months (s_t from PBS reviews).
`python scripts/nowcast.py live` issues this month's forecast from the weekly archive.
"""
import csv, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import dm_hln, f, shift  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIRST_TRAIN = "2019-08"
FIRST_LIVE = "2026-10"
PKT = timezone(timedelta(hours=5))


def load():
    cpi = {r["month"]: r for r in csv.DictReader(open(ROOT / "data/cpi/monthly.csv", encoding="utf-8"))}
    spi = {r["month"]: float(r["spi_mom"]) for r in csv.DictReader(open(ROOT / "data/cpi/spi_monthly.csv", encoding="utf-8"))}
    return cpi, spi


def fit(cpi, spi, t):
    """(a, b, n) from every month in [FIRST_TRAIN, t-1] with both figures."""
    xs, ys = [], []
    k = FIRST_TRAIN
    while k < t:
        if k in spi and f(cpi.get(k, {}).get("mom_new")) is not None:
            xs.append(spi[k]); ys.append(f(cpi[k]["mom_new"]))
        k = shift(k, 1)
    b, a = np.polyfit(xs, ys, 1)
    return float(a), float(b), len(xs)


def forecast(cpi, spi_t, a, b, t):
    prev = cpi[shift(t, -1)]
    yoy_prev = f(prev["yoy_first"]) if prev["yoy_first"] else f(prev["yoy_later"])
    mom_ly = f(cpi[shift(t, -12)]["mom_new"])
    m_hat = a + b * spi_t
    return ((1 + yoy_prev / 100) * (1 + m_hat / 100) / (1 + mom_ly / 100) - 1) * 100, m_hat


def backtest():
    cpi, spi = load()
    scored = list(csv.DictReader(open(ROOT / "results/scored_rows.csv", encoding="utf-8")))
    rows, excluded = [], []
    for r in scored:
        t = r["target"]
        if t not in spi:
            excluded.append((t, "spi_not_found"))
            continue
        a, b, n = fit(cpi, spi, t)
        yhat, m_hat = forecast(cpi, spi[t], a, b, t)
        rows.append({"target": t, "actual": float(r["actual"]), "tally": round(yhat, 3), "b2": float(r["b2"]),
                     "ministry": float(r["ministry"]), "a": round(a, 3), "b": round(b, 3), "n_train": n,
                     "flags": r["flags"]})
    act = np.array([r["actual"] for r in rows])
    err = {k: np.array([r[k] for r in rows]) - act for k in ("tally", "b2", "ministry")}
    res = {"n": len(rows), "excluded": excluded,
           "mae": {k: round(float(np.abs(e).mean()), 3) for k, e in err.items()},
           "rmse": {k: round(float(np.sqrt((e ** 2).mean())), 3) for k, e in err.items()},
           "bias": {k: round(float(e.mean()), 3) for k, e in err.items()}}
    for other in ("b2", "ministry"):
        hln, p, dbar = dm_hln(err["tally"], err[other])
        w = stats.wilcoxon(np.abs(err["tally"]), np.abs(err[other]))
        res[f"vs_{other}"] = {"dm_hln": round(hln, 3), "p": round(p, 4), "mean_abs_diff_tally_minus": round(dbar, 3),
                              "wilcoxon_p": round(float(w.pvalue), 4)}
    hln, p, dbar = res["vs_b2"]["dm_hln"], res["vs_b2"]["p"], res["vs_b2"]["mean_abs_diff_tally_minus"]
    res["verdict_vs_b2"] = ("TALLY BEATS B2" if dbar < 0 else "TALLY WORSE THAN B2") if p < 0.05 else "NO SIGNIFICANT DIFFERENCE"
    res["note"] = "Backtest: s_t sees every week of the month (Amendment 1 §4). Optimistic by construction; not a record."
    (ROOT / "results/nowcast_backtest.json").write_text(json.dumps(res, indent=2))
    with open(ROOT / "results/nowcast_backtest_rows.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(json.dumps(res, indent=2))


def live():
    """Issue this month's forecast on its last day (PKT), from weeks archived so far."""
    now = datetime.now(PKT)
    t = now.strftime("%Y-%m")
    if (now + timedelta(days=1)).month == now.month and "--force" not in sys.argv:
        print("not the last day of the month; nothing to issue")
        return
    out = ROOT / "data/live/forecasts.csv"
    if out.exists() and any(r["target"] == t for r in csv.DictReader(open(out, encoding="utf-8"))):
        print(f"{t} already issued")
        return
    weeks = [r for r in csv.DictReader(open(ROOT / "data/live/spi_weekly.csv", encoding="utf-8"))]
    cur = [float(r["index"]) for r in weeks if r["week_ending"][:7] == t]
    prv = [float(r["index"]) for r in weeks if r["week_ending"][:7] == shift(t, -1)]
    row = {"target": t, "issued_pkt": now.isoformat(timespec="seconds"), "weeks_current": len(cur),
           "weeks_previous": len(prv), "spi_mom": "", "a": "", "b": "", "forecast_yoy": "", "status": ""}
    if len(cur) < 2 or len(prv) < 2:
        row["status"] = "missed: fewer than two archived weeks"  # Amendment 1 §4: recorded, not filled
    else:
        cpi, spi = load()
        s_t = (np.mean(cur) / np.mean(prv) - 1) * 100
        a, b, _ = fit(cpi, spi, t)
        yhat, _ = forecast(cpi, s_t, a, b, t)
        # Amendment 1 §6: the record starts with October 2026; earlier issues are rehearsals, never scored
        status = "issued" if t >= FIRST_LIVE else "rehearsal: before first live target"
        row.update(spi_mom=round(float(s_t), 3), a=round(a, 4), b=round(b, 4), forecast_yoy=round(float(yhat), 2), status=status)
    new = not out.exists()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=row.keys())
        if new:
            w.writeheader()
        w.writerow(row)
    print(row)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    {"backtest": backtest, "live": live}[sys.argv[1]]()
