"""Build the Finance Ministry forecast register (PREREGISTRATION.md §3–4).

The judgements — target month, form, bounds, admit or exclude — are made by hand in ROWS below.
The quote, page and file hash are NOT typed: they are found in the PDF by a needle, and the
script fails if the needle is absent or the typed numbers do not appear in the quote. So a
row cannot claim words or numbers the document does not contain.

Run once, commit the output, and only then join any actual CPI figure (§4).
"""
import csv, hashlib, re, sys, unicodedata
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"

# (file, target, form, lo, hi, ref_month, status, reason, needle, flags)
# form: range | point | relative | none. Excluded rows keep their numbers when the text has them.
ROWS = [
    ("economic_updates_march_2020.pdf", "2020-03", "none", None, None, None, "excluded", "no_numeric_forecast", None, ""),
    ("economic_updates_april_2020.pdf", "2020-04", "none", None, None, None, "excluded", "no_numeric_forecast", None, ""),
    ("economic_updates_may_2020.pdf", "2020-05", "none", None, None, None, "excluded", "no_numeric_forecast", None, ""),
    ("economic_updates_june_2020.pdf", "2020-06", "point", 10.7, 10.7, None, "excluded", "target_is_fiscal_year_average", "expected to remain at 10.7%", ""),
    ("economic_updates_july_2020.pdf", "2020-07", "none", None, None, None, "excluded", "no_numeric_forecast", None, "second_document_same_month"),
    ("monthly_outlook_Jul_2020.pdf", "2020-07", "range", 7.6, 9.3, None, "admitted", "", "margin of 7.6", ""),
    ("economic_updates_and_outlook_august_2020.pdf", "2020-08", "range", 8.4, 9.7, None, "admitted", "", "range of 8.4 to 9.7", ""),
    ("economic_updates_and_outlook_september_2020.pdf", "2020-09", "range", 7.8, 9.0, None, "admitted", "", "range of 7.8 to 9.0", ""),
    ("economic_update_october_2020.pdf", "2020-10", "none", None, None, None, "excluded", "no_numeric_forecast", None, ""),
    ("economic_update_november_2020.pdf", "2020-11", "range", 7.6, 9.0, None, "admitted", "", "settle around 8.5", "also_states_point_8.5"),
    ("economic_update_december_2020.pdf", "2020-12", "range", 7.8, 8.3, None, "admitted", "", "range of 7.8 and 8.3", ""),
    ("economic_update_january_2021.pdf", "2021-01", "range", 7.2, 8.2, None, "admitted", "", "range of 7.2 to 8.2", ""),
    ("economic_update_february_2021.pdf", "2021-02", "range", 5.5, 7.5, None, "excluded", "target_month_ambiguous_next_month", "for next month may remain", ""),
    ("economic_update_march_2021.pdf", "2021-03", "range", 7.9, 9.5, None, "excluded", "target_month_ambiguous_next_month", "For next month it is expected", ""),
    ("economic_update_april_2021.pdf", "2021-04", "range", 8.0, 9.5, None, "excluded", "target_month_ambiguous_next_month", "percent next month", "recovered_from_wayback_20210501030402"),
    ("economic_update_may_2021.pdf", "2021-05", "range", 9.0, 9.8, None, "admitted", "", "settle between 9.0", ""),
    ("economic_update_june_2021.pdf", "2021-06", "range", 8.8, 10.2, None, "admitted", "", "probability margins of", "also_states_conditional_point_9.8"),
    ("economic_update_july_2021.pdf", "2021-07", "range", 7.5, 9.0, None, "admitted", "", "range of 7.5", ""),
    ("economic_update_August_2021.pdf", "2021-08", "range", 7.6, 9.2, None, "admitted", "", "level attained in July within a range", ""),
    ("economic_update_September_2021.pdf", "2021-09", "range", 7.5, 8.4, None, "admitted", "", "7.5 to 8.4", ""),
    ("economic_update_October_2021.pdf", "2021-10", "none", None, None, None, "excluded", "directional_only", "settle below the level observed in September", ""),
    ("economic_update_November_2021.pdf", "2021-11", "range", 8.5, 9.5, None, "admitted", "", "may remain 8.5 to 9.5", ""),
    ("economic_update_December_2021.pdf", "2021-12", "none", None, None, None, "excluded", "directional_only", "slightly less than the last month", ""),
    ("economic_update_january_2022.pdf", "2022-01", "none", None, None, None, "excluded", "directional_only", "may slightly increase", ""),
    ("economic_update_February_2022.pdf", "2022-02", "none", None, None, None, "excluded", "directional_only", "expected to decelerate", ""),
    ("economic_update_March_2022.pdf", "2022-03", "range", 9.5, 11.5, None, "admitted", "", "9.5 to 11.5 percent territory", "month_inferred"),
    ("economic_update_April_2022.pdf", "2022-04", "range", 11.5, 12.5, None, "admitted", "", "range of 11.5 to 12.5", ""),
    ("economic_update_may_2022.pdf", "2022-05", "range", 12.5, 13.8, None, "admitted", "", "between 12.5 and 13.8", ""),
    ("economic_update_June_2022.pdf", "2022-06", "range", 14.5, 15.5, None, "admitted", "", "range of 14.5", ""),
    ("economic_update_July_2022.pdf", "2022-07", "relative", None, None, "2022-06", "admitted", "", "hoover around", ""),
    ("economic_update_August_2022.pdf", "2022-08", "relative", None, None, "2022-07", "admitted", "", "nearly the same level", ""),
    ("economic_update_September_2022.pdf", "2022-09", "none", None, None, None, "excluded", "directional_only", "halt to the recent drastic accelerations", ""),
    ("economic_update_October_2022.pdf", "2022-10", "range", 21.0, 22.5, None, "admitted", "", "range of 21- 22.5", "month_inferred"),
    ("economic_update_November_2022.pdf", "2022-11", "range", 23.0, 25.0, None, "admitted", "", "range of 23-25", ""),
    ("economic_update_December_2022.pdf", "2022-12", "range", 21.0, 23.0, None, "admitted", "", "range of 21-23", "month_inferred"),
    ("economic_update_January_2023.pdf", "2023-01", "range", 24.0, 26.0, None, "admitted", "", "range of 24-26", ""),
    ("economic_update_February_2023.pdf", "2023-02", "range", 28.0, 30.0, None, "excluded", "target_month_ambiguous_coming_months", "28 to 30 percent in coming months", ""),
    ("economic_update_March_2023.pdf", "2023-03", "none", None, None, None, "excluded", "no_numeric_forecast", None, ""),
    ("economic_update_April_2023.pdf", "2023-04", "none", None, None, None, "excluded", "text_not_machine_readable", None, "text_drawn_as_vector_shapes"),
    ("economic_update_May_2023.pdf", "2023-05", "range", 34.0, 36.0, None, "admitted", "", "range of 34-36", ""),
    ("economic_update_June_2023.pdf", "2023-06", "range", 31.0, 33.0, None, "admitted", "", "range of 31-33", ""),
    ("economic_update_July_2023.pdf", "2023-07", "range", 25.0, 27.0, None, "admitted", "", "range of 25-27", ""),
    ("economic_update_August_2023.pdf", "2023-08", "range", 29.0, 31.0, None, "admitted", "", "around 29 to 31 percent in August", "pdf_created_after_month_end"),
    ("economic_update_September_2023.pdf", "2023-09", "range", 29.0, 31.0, None, "admitted", "", "In September 2023, it is expected", ""),
    ("economic_update_October_2023.pdf", "2023-10", "range", 27.0, 29.0, None, "admitted", "", "around 27 to 29", ""),
    ("economic_update_November_2023.pdf", "2023-11", "range", 26.5, 27.5, None, "admitted", "", "around 26.5-27.5", ""),
    ("economic_update_December_2023.pdf", "2023-12", "range", 27.5, 28.5, None, "admitted", "", "27.5-28.5 percent in December", ""),
    ("economic_update_January_2024.pdf", "2024-01", "range", 27.5, 28.5, None, "admitted", "", "27.5-28.5 percent in January", ""),
    ("economic_update_February_2024.pdf", "2024-02", "range", 24.5, 25.5, None, "admitted", "", "24.5-25.5", "pdf_created_after_month_end"),
    ("economic_update_March_2024.pdf", "2024-03", "range", 22.5, 23.5, None, "admitted", "", "22.5- 23.5", ""),
    ("economic_update_April_2024.pdf", "2024-04", "range", 18.5, 19.5, None, "admitted", "", "18.5- 19.5", ""),
    ("economic_update_May_2024.pdf", "2024-05", "range", 13.5, 14.5, None, "admitted", "", "13.5-14.5", ""),
    ("economic_update_June_2024.pdf", "2024-06", "range", 12.5, 13.5, None, "admitted", "", "12.5-13.5", ""),
    ("economic_update_July_2024.pdf", "2024-07", "none", None, None, None, "excluded", "no_numeric_forecast", None, ""),
    ("economic_update_August_2024.pdf", "2024-08", "none", None, None, None, "excluded", "no_numeric_forecast", None, ""),
    ("economic_update_September_2024.pdf", "2024-09", "none", None, None, None, "excluded", "directional_only", "further decrease is anticipated", ""),
    ("economic_update_October_2024.pdf", "2024-10", "range", 6.0, 7.0, None, "admitted", "", "range of 6-7%", ""),
    ("economic_update_November_2024.pdf", "2024-11", "range", 5.8, 6.8, None, "admitted", "", "5.8% - 6.8%", ""),
    ("economic_update_December_2024.pdf", "2024-12", "range", 4.0, 5.0, None, "admitted", "", "4.0- 5.0 percent for December", ""),
    ("economic_update_February_2025.pdf", "2025-02", "range", 2.0, 3.0, None, "admitted", "", "2.0-3.0 percent for February", ""),
    ("economic_update_March_2025.pdf", "2025-03", "range", 1.0, 1.5, None, "admitted", "", "1.0-1.5 percent for March", ""),
    ("economic_update_april_2025.pdf", "2025-04", "range", 1.5, 2.0, None, "admitted", "", "1.5 - 2.0 percent in April", ""),
    ("economic_update_n_outlook_may2025.pdf", "2025-05", "range", 1.5, 2.0, None, "admitted", "", "1.5 - 2.0 percent in May", ""),
    ("economic_outlook_june2025.pdf", "2025-06", "range", 3.0, 4.0, None, "admitted", "", "3.0-4.0 percent for June", ""),
    ("economic_outlook_july2025.pdf", "2025-07", "range", 3.5, 4.5, None, "admitted", "", "within 3.5 to 4.5", "month_inferred"),
    ("economic_outlook_august2025.pdf", "2025-08", "range", 4.0, 5.0, None, "admitted", "", "4.0-5.0 percent in August", ""),
    ("economic_update_outlook_sep_2025.pdf", "2025-09", "range", 3.5, 4.5, None, "admitted", "", "4.5 percent range in September", ""),
    ("economic_update_outlook_oct_2025.pdf", "2025-10", "range", 5.0, 6.0, None, "admitted", "", "5-6 percent in October", ""),
    ("economic_update_outlook_nov_2025.pdf", "2025-11", "range", 5.0, 6.0, None, "admitted", "", "5.0-6.0 percent in November", ""),
    ("economic_update_outlook_dec_2025.pdf", "2025-12", "range", 5.5, 6.5, None, "admitted", "", "5.5-6.5 percent in December", ""),
    ("economic_update_outlook_jan_2026.pdf", "2026-01", "range", 5.0, 6.0, None, "admitted", "", "5.0-6.0 percent in January", ""),
    ("economic_update_outlook_feb_2026.pdf", "2026-02", "range", 6.0, 7.0, None, "admitted", "", "6.0-7.0 percent in February", ""),
    ("economic_update_outlook_mar_2026.pdf", "2026-03", "range", 7.5, 8.5, None, "admitted", "", "7.5-8.5 percent for March", ""),
    ("Monthly_Economic_Update_and_Outlook_April_2026.pdf", "2026-04", "range", 8.0, 9.0, None, "admitted", "", "8.0-9.0 percent for April", ""),
    ("Monthly_Economic_Update_and_Outlook_May_2026.pdf", "2026-05", "none", None, None, None, "excluded", "no_numeric_forecast", "remain in the target range in FY2026", ""),
    ("Monthly_Economic_Update_and_Outlook_June_2026.pdf", "2026-06", "range", 11.0, 12.0, None, "admitted", "", "11-12 percent for June", ""),
    ("Monthly_Economic_Update_and_Outlook_July_2026.pdf", "2026-07", "range", 9.0, 10.0, None, "admitted", "", "9.0-10.0 percent in July", ""),
    ("Monthly_Economic_Update_and_Outlook_August_2026.pdf", "2026-08", "range", 10.0, 11.0, None, "admitted", "", "range of 10 to 11", ""),
]


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).replace("−", "-")


def num_in(x, text):
    """True if x appears as a number in text: 21.0 matches '21' or '21.0', not '121'."""
    pat = r"(?<![\d.])" + (str(int(x)) + r"(\.0)?" if x == int(x) else re.escape(str(x))) + r"(?![\d])"
    return re.search(pat, text) is not None


def find(pdf, needle):
    for i, p in enumerate(pdf.pages, 1):
        t = norm(p.extract_text() or "")
        j = t.find(needle)
        if j >= 0:
            # widen to the enclosing sentence, without splitting on decimal points
            a = max(t.rfind(". ", 0, j), t.rfind("▪", 0, j), t.rfind("§", 0, j)) + 1
            m = re.search(r"\.(\s+(?=[A-Z0-9])|$)", t[j + len(needle):])
            b = j + len(needle) + (m.start() + 1 if m else 200)
            return i, t[a:b].strip()
    return None, None


def main():
    out, errors = [], []
    seen_admitted = set()
    for file, target, form, lo, hi, ref, status, reason, needle, flags in ROWS:
        path = RAW / file
        data = path.read_bytes()
        pdf = pypdf.PdfReader(path)
        created = str((pdf.metadata or {}).get("/CreationDate", ""))[2:10]
        page, quote = find(pdf, needle) if needle else (None, "")
        if needle and page is None:
            errors.append(f"{file}: needle not found: {needle!r}")
        for x in (lo, hi):
            if x is not None and quote and not num_in(x, quote):
                errors.append(f"{file}: {x} not in quote")
        if status == "admitted":
            if target in seen_admitted:
                errors.append(f"{target}: two admitted rows")
            seen_admitted.add(target)
        point = (lo + hi) / 2 if lo is not None else None
        out.append({
            "target_month": target, "status": status, "exclusion_reason": reason, "form": form,
            "lo": lo, "hi": hi, "point": point, "width": None if lo is None else round(hi - lo, 2),
            "relative_to": ref or "", "flags": flags, "quote": quote, "page": page or "",
            "file": file, "sha256": hashlib.sha256(data).hexdigest(), "pdf_created": created,
        })
    if errors:
        sys.exit("\n".join(errors))
    dest = ROOT / "data/register/ministry_forecasts.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out[0].keys())
        w.writeheader(); w.writerows(out)
    adm = [r for r in out if r["status"] == "admitted"]
    reasons = {}
    for r in out:
        if r["status"] == "excluded":
            reasons[r["exclusion_reason"]] = reasons.get(r["exclusion_reason"], 0) + 1
    print(f"{len(out)} rows, {len(adm)} admitted, excluded by reason: {reasons}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
