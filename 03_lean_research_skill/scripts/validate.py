"""Validate worker output TSVs. No LLM.
usage: python -I validate.py --dir <working folder>
Reads out/*.tsv, writes validated.tsv (passing rows, plus batch_id and src_domain) and failed.tsv (row + reasons).
Worker columns (19): contact_id, opener, bridge, workload, wclass, hook_grade, source_url, evidence, ev,
d_loc, d_hook, d_compute, d_status, variant, playbook_ver, searches, fetches, src_type, class_src_url
Rows with only the first 13 columns are still accepted (older format).
"""
import argparse, csv, glob, os, re
from urllib.parse import urlparse

COLS = ["contact_id", "opener", "bridge", "workload", "wclass", "hook_grade", "source_url", "evidence", "ev",
        "d_loc", "d_hook", "d_compute", "d_status", "variant", "playbook_ver", "searches", "fetches", "src_type",
        "class_src_url"]
BANNED = re.compile(r"\b(aws|gcp|azure|google cloud|amazon web|free|discount|pricing|price|cheaper)\b|\$|i came across|linkedin\.com", re.I)
SENSITIVE = re.compile(r"condolence|passed away|divorce|pregnan|funeral|diagnosed", re.I)
COMPLIANCE_OK = re.compile(r"(synthetic or de-identified|public or de-identified|non-sensitive)", re.I)


def words(s):
    return len(s.split())


def domain(u):
    try:
        h = urlparse(u).netloc.lower()
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""


def check(r, compliance):
    why = []
    o, b, w = r["opener"], r["bridge"], r["workload"]
    if not o:
        return ["no opener"]
    if not (15 <= words(o) <= 35):
        why.append(f"opener words {words(o)}")
    if not (10 <= words(b) <= 45):
        why.append(f"bridge words {words(b)}")
    if not (2 <= words(w) <= 6) or w != w.lower():
        why.append("workload form")
    for name, txt in (("opener", o), ("bridge", b), ("workload", w)):
        if BANNED.search(txt):
            why.append(f"banned term in {name}")
        if SENSITIVE.search(txt):
            why.append(f"sensitive term in {name}")
        for q in re.findall(r'"([^"]+)"', txt):
            if words(q) >= 15:
                why.append("quote too long")
    if re.search(r"\bhipaa\b", b, re.I) and "not a HIPAA environment" not in b:
        why.append("hipaa mention form")
    if compliance and not COMPLIANCE_OK.search(b):
        why.append("compliance sentence missing")
    if r["hook_grade"] in ("P", "F", "C"):
        if not r["source_url"].startswith("http"):
            why.append("no source_url")
        if not r["evidence"] or words(r["evidence"]) > 25:
            why.append("evidence missing or long")
    else:
        why.append("no hook")
    if r["wclass"] not in ("heavy", "light"):
        why.append("wclass")
    return why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    comp = {}
    qp = os.path.join(a.dir, "queue.csv")
    if os.path.exists(qp):
        for r in csv.DictReader(open(qp, newline="", encoding="utf-8")):
            comp[r["contact_id"]] = r["compliance"] == "1"
    good, bad = [], []
    for p in sorted(glob.glob(os.path.join(a.dir, "out", "*.tsv"))):
        bid = os.path.basename(p)[4:-4]
        for line in csv.reader(open(p, encoding="utf-8"), delimiter="\t"):
            if not line:
                continue
            line = (line + [""] * len(COLS))[: len(COLS)]
            r = dict(zip(COLS, line))
            r["batch_id"] = bid
            r["src_domain"] = domain(r["source_url"])
            why = check(r, comp.get(r["contact_id"], False))
            (bad if why else good).append((r, why))
    out_cols = COLS + ["batch_id", "src_domain"]
    with open(os.path.join(a.dir, "validated.tsv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        for r, _ in good:
            w.writerow([r[c] for c in out_cols])
    with open(os.path.join(a.dir, "failed.tsv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        for r, why in bad:
            w.writerow([r[c] for c in out_cols] + ["; ".join(why)])
    tot = len(good) + len(bad)
    hooks = sum(1 for r, _ in good if r["hook_grade"] in ("P", "F"))
    print(f"rows {tot}, pass {len(good)} ({100*len(good)//max(tot,1)}%), pass with P/F hook {hooks}, failed {len(bad)}")


if __name__ == "__main__":
    main()
