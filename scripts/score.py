"""Score the Finance Ministry against B1 and B2, exactly as PREREGISTRATION.md §5–7 fix it.

B2's identity: the pre-registration projects the index, I_t = I_{t-1} * (1 + mbar), then takes
I_t / I_{t-12}. Since I_{t-1} / I_{t-12} = (1 + YoY_{t-1}) / (1 + MoM_{t-12}), that is
    YoY_t = (1 + YoY_{t-1}) * (1 + mbar) / (1 + MoM_{t-12}) - 1,
which needs published rates only — no index level is re-derived across the base change.
The forecast is identical; see FINDINGS.md.
"""
import csv, json, sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
MIN_ROWS = 40  # §6
REGIME = 15.0  # §7


def shift(m, k):
    y, mo = map(int, m.split("-"))
    i = y * 12 + mo - 1 + k
    return f"{i // 12}-{i % 12 + 1:02d}"


def f(x):
    return float(x) if x not in ("", None) else None


def dm_hln(e1, e2):
    """Diebold-Mariano on absolute-error differences, h = 1, Harvey-Leybourne-Newbold correction."""
    d = np.abs(e1) - np.abs(e2)
    n = len(d)
    dm = d.mean() / np.sqrt(d.var(ddof=0) / n)
    hln = dm * np.sqrt((n - 1) / n)  # (n + 1 - 2h + h(h-1)/n) / n with h = 1
    p = 2 * stats.t.sf(abs(hln), df=n - 1)
    return float(hln), float(p), float(d.mean())


def score(rows, label):
    a = np.array([r["actual"] for r in rows])
    out = {"label": label, "n": len(rows)}
    for k in ("ministry", "b1", "b2"):
        e = np.array([r[k] for r in rows]) - a
        out[k] = {"mae": round(float(np.abs(e).mean()), 3), "rmse": round(float(np.sqrt((e ** 2).mean())), 3),
                  "bias": round(float(e.mean()), 3)}
    rng = [r for r in rows if r["form"] == "range"]
    out["range_hit_rate"] = round(sum(r["lo"] <= r["actual"] <= r["hi"] for r in rng) / len(rng), 3) if rng else None
    out["range_n"] = len(rng)
    return out


def main():
    cpi = {r["month"]: r for r in csv.DictReader(open(ROOT / "data/cpi/monthly.csv", encoding="utf-8"))}
    reg = list(csv.DictReader(open(ROOT / "data/register/ministry_forecasts.csv", encoding="utf-8")))
    rows, dropped, detail = [], [], []
    for r in reg:
        if r["status"] != "admitted":
            continue
        t = r["target_month"]
        actual = f(cpi[t]["yoy_first"])
        if actual is None:
            dropped.append((t, "first_release_not_found"))
            continue
        if r["form"] == "relative":
            point = f(cpi[r["relative_to"]]["yoy_first"])
            if point is None:
                dropped.append((t, "relative_reference_not_found"))
                continue
        else:
            point = f(r["point"])
        prev = cpi[shift(t, -1)]
        yoy_prev = f(prev["yoy_first"]) if prev["yoy_first"] else f(prev["yoy_later"])
        moms = [f(cpi[shift(t, -12 * k)]["mom_pub"]) for k in range(1, 6)]
        mom_ly = f(cpi[shift(t, -12)]["mom_new"])
        if yoy_prev is None or mom_ly is None or None in moms:
            dropped.append((t, "baseline_input_missing"))
            continue
        mbar = sum(moms) / 5
        b2 = ((1 + yoy_prev / 100) * (1 + mbar / 100) / (1 + mom_ly / 100) - 1) * 100
        row = {"target": t, "actual": actual, "ministry": point, "b1": yoy_prev, "b2": round(b2, 3),
               "form": r["form"], "lo": f(r["lo"]), "hi": f(r["hi"]), "flags": r["flags"],
               "b1_src": "first" if prev["yoy_first"] else "later_vintage",
               "mom_srcs": ",".join(cpi[shift(t, -12 * k)]["mom_pub_src"] for k in range(1, 6))}
        rows.append(row)
        detail.append(row)

    res = {"admitted_in_register": sum(r["status"] == "admitted" for r in reg), "scored": len(rows), "dropped": dropped}
    if len(rows) < MIN_ROWS:
        res["primary"] = f"UNDERPOWERED: {len(rows)} < {MIN_ROWS} rows; test not run (§6)"
    else:
        m = np.array([r["ministry"] for r in rows]) - np.array([r["actual"] for r in rows])
        b = np.array([r["b2"] for r in rows]) - np.array([r["actual"] for r in rows])
        hln, p, dbar = dm_hln(m, b)
        w = stats.wilcoxon(np.abs(m), np.abs(b))
        verdict = ("MINISTRY BEATS B2" if dbar < 0 else "MINISTRY WORSE THAN B2") if p < 0.05 else "NO SIGNIFICANT DIFFERENCE"
        res["primary"] = {"dm_hln": round(hln, 3), "p": round(p, 4), "mean_abs_err_diff_ministry_minus_b2": round(dbar, 3),
                          "wilcoxon_stat": float(w.statistic), "wilcoxon_p": round(float(w.pvalue), 4), "verdict": verdict}
    res["all"] = score(rows, "all admitted")
    # F4 commitment: always shown without the two issues whose PDFs postdate their month
    clean = [r for r in rows if "pdf_created_after_month_end" not in r["flags"]]
    res["without_F4_rows"] = score(clean, "excluding pdf_created_after_month_end")
    if len(clean) >= MIN_ROWS:
        m = np.array([r["ministry"] - r["actual"] for r in clean]); b = np.array([r["b2"] - r["actual"] for r in clean])
        hln, p, dbar = dm_hln(m, b)
        res["without_F4_rows"]["dm_hln"], res["without_F4_rows"]["p"] = round(hln, 3), round(p, 4)
    # §7 secondary splits: descriptive only
    res["regime_high"] = score([r for r in rows if r["actual"] >= REGIME], f"actual >= {REGIME}")
    res["regime_low"] = score([r for r in rows if r["actual"] < REGIME], f"actual < {REGIME}")
    up = [r for r in rows if r["actual"] > r["b1"]]; dn = [r for r in rows if r["actual"] < r["b1"]]
    res["inflation_rose"] = score(up, "actual above last month") if up else None
    res["inflation_fell"] = score(dn, "actual below last month") if dn else None
    for form in ("range", "relative"):
        sub = [r for r in rows if r["form"] == form]
        res[f"form_{form}"] = score(sub, form) if sub else None

    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/primary.json").write_text(json.dumps(res, indent=2))
    with open(ROOT / "results/scored_rows.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=detail[0].keys()); w.writeheader(); w.writerows(detail)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
