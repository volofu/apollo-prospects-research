"""Merge validated research with fallbacks into an Apollo import CSV keyed on Email. No LLM.
usage: python -I build_import.py --dir <working folder>
Writes fields_for_import.csv (Email, opener, bridge, workload, credit_compute, spend_sentence, Enrichment flags)
and sheet_log.csv (contact_id, email, rank, tier, hook_grade, class, source_url, d_loc, d_hook, d_compute, d_status).
Never writes rows for contacts missing from queue.csv (queue.csv only holds Apollo-verified emails).
"""
import argparse, csv, os

HEAVY_CC = "about 22 hours on an 8x A100 80GB node"
LIGHT_CC = "about 40 hours on a 4x L40 node"
SPEND = ("For reference, a typical seed-stage startup running GPUs on a hyperscaler pays around $8-20K a month, "
         "and even our list rates, without the startup discounts, would save $2.5-8K of that. By Series B the same "
         "bill is often $50-200K a month, so the savings grow to $15-60K, which is why switching early is easier "
         "than switching later.")
COLS = ["contact_id", "opener", "bridge", "workload", "wclass", "hook_grade", "source_url", "evidence", "ev",
        "d_loc", "d_hook", "d_compute", "d_status"]


def flags(d_loc, d_hook, d_compute, d_status, grade):
    parts = []
    if d_loc and d_loc != "none":
        parts.append(f"DUBIOUS-LOCATION: {d_loc}")
    if (d_hook and d_hook != "none") or grade not in ("P", "F"):
        parts.append(f"DUBIOUS-HOOK: {d_hook if d_hook and d_hook != 'none' else 'company-level or scripted opener'}")
    if d_compute and d_compute != "none":
        parts.append(f"DUBIOUS-COMPUTE: {d_compute}")
    if d_status and d_status != "none":
        parts.append(f"DUBIOUS-STARTUP-STATUS: {d_status}")
    return ". ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    res = {}
    vp = os.path.join(a.dir, "validated.tsv")
    if os.path.exists(vp):
        for line in csv.reader(open(vp, encoding="utf-8"), delimiter="\t"):
            if line:
                line = (line + [""] * len(COLS))[: len(COLS)]
                res[line[0]] = dict(zip(COLS, line))
    imp, log = [], []
    for q in csv.DictReader(open(os.path.join(a.dir, "queue.csv"), newline="", encoding="utf-8")):
        if q["hold"] == "1":
            continue
        r = res.get(q["contact_id"])
        if r:
            op, br, wl, cl, grade = r["opener"], r["bridge"], r["workload"], r["wclass"], r["hook_grade"]
            tier = "R1-" + (r["ev"] or "search")
            fl = flags(r["d_loc"], r["d_hook"], r["d_compute"], r["d_status"], grade)
            url = r["source_url"]
            d = (r["d_loc"], r["d_hook"], r["d_compute"], r["d_status"])
        else:
            op, br, wl, cl, grade = q["fb_opener"], q["fb_bridge"], q["fb_workload"], q["class"], "NONE"
            tier, url, d = "B-scripted", "", ("", "", "", "")
            fl = flags("", "", "", "", grade)
        imp.append({"Email": q["email"], "opener": op, "bridge": br, "workload": wl,
                    "credit_compute": HEAVY_CC if cl == "heavy" else LIGHT_CC, "spend_sentence": SPEND,
                    "Enrichment flags": fl})
        log.append([q["contact_id"], q["email"], q["rank"], tier, grade, cl, url, *d])
    with open(os.path.join(a.dir, "fields_for_import.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Email", "opener", "bridge", "workload", "credit_compute", "spend_sentence", "Enrichment flags"])
        w.writeheader()
        w.writerows(imp)
    with open(os.path.join(a.dir, "sheet_log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["contact_id", "email", "rank", "tier", "hook_grade", "class", "source_url", "d_loc", "d_hook", "d_compute", "d_status"])
        w.writerows(log)
    r1 = sum(1 for l in log if l[3].startswith("R1"))
    print(f"import rows {len(imp)} (researched {r1}, scripted fallback {len(imp)-r1})")


if __name__ == "__main__":
    main()
