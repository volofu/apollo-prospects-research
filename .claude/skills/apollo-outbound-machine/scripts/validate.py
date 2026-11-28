"""Validate merged research rows. No LLM.  usage: validate.py --dir D
Reads D/research.tsv + D/contacts.tsv. Writes D/validated.tsv (pass) and D/failed.tsv (row + reasons).
A failed row is NOT an error for the contact: build_import.py gives it the honest fallback copy.
"""
import argparse, csv, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import words

COLS = ["contact_id", "opener", "bridge", "workload", "wclass", "hook_grade", "source_url", "evidence", "ev",
        "d_loc", "d_hook", "d_compute", "d_status", "variant", "playbook_ver", "searches", "fetches", "src_type",
        "class_src_url"]
BANNED = re.compile(r"\b(aws|gcp|azure|google cloud|amazon web|free|discount|pricing|price|cheaper)\b|\$|i came across|linkedin\.com", re.I)
SENSITIVE = re.compile(r"condolence|passed away|divorce|pregnan|funeral|diagnosed", re.I)
COMPLIANCE_OK = re.compile(r"(synthetic or de-identified|public or de-identified|non-sensitive)", re.I)


def check(r, c):
    why = []
    o, b, w = r["opener"], r["bridge"], r["workload"]
    if not o:
        return ["no opener"]
    if not (15 <= words(o) <= 35): why.append(f"opener words {words(o)}")
    if not re.match(r"I (read|saw|heard|listened)\b", o): why.append("opener start")
    if not (10 <= words(b) <= 45): why.append(f"bridge words {words(b)}")
    if "I'd guess" not in b: why.append("bridge not hedged")
    if not (2 <= words(w) <= 6) or w != w.lower(): why.append("workload form")
    if BANNED.search(o + " " + b): why.append("banned term")
    if SENSITIVE.search(o): why.append("sensitive opener")
    if c.get("compliance") == "1" and not COMPLIANCE_OK.search(b): why.append("compliance sentence missing")
    # the opener must talk TO the recipient, never ABOUT them by name (reads as a stranger)
    fn, ln = c["first"].strip(), c["last"].strip()
    if fn and re.search(r"\b" + re.escape(fn) + r"\b", o): why.append("recipient named in opener (use you/your)")
    if ln and len(ln) > 2 and re.search(r"\b" + re.escape(ln) + r"\b", o) and ln.lower() not in c["company"].lower():
        why.append("recipient surname in opener")
    for q in re.findall(r'"([^"]+)"', o):
        if words(q) >= 15: why.append("long quote")
    if r["hook_grade"] not in ("P", "F", "C", "NONE"): why.append("hook_grade")
    return why


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); a = ap.parse_args()
    contacts = {r["contact_id"]: r for r in csv.DictReader(open(os.path.join(a.dir, "contacts.tsv"), newline="", encoding="utf-8"), delimiter="\t")}
    ok = fail = pf = 0
    reasons = {}
    with open(os.path.join(a.dir, "validated.tsv"), "w", encoding="utf-8") as vf, open(os.path.join(a.dir, "failed.tsv"), "w", encoding="utf-8") as ff:
        for line in open(os.path.join(a.dir, "research.tsv"), encoding="utf-8"):
            f = (line.rstrip("\n").split("\t") + [""] * 19)[:19]
            r = dict(zip(COLS, f)); c = contacts.get(r["contact_id"])
            if not c: continue
            why = check(r, c)
            if why:
                fail += 1; ff.write("\t".join(f) + "\t" + "; ".join(why) + "\n")
                for w_ in why: reasons[w_.split(" ")[0] + " " + (w_.split(" ")[1] if " " in w_ else "")] = reasons.get(w_.split(" ")[0] + " " + (w_.split(" ")[1] if " " in w_ else ""), 0) + 1
            else:
                ok += 1; vf.write("\t".join(f) + "\n"); pf += r["hook_grade"] in ("P", "F")
    print(f"rows {ok+fail} pass {ok} ({ok*100//max(ok+fail,1)}%) pass with P/F hook {pf} failed {fail} reasons {reasons}")
