"""Build the Apollo field-import CSV. No LLM, no network.  usage: build_import.py --dir D [--funding funding.tsv]
Reads D/contacts.tsv, D/validated.tsv, optional funding.tsv (see funding_prompt.md). Writes D/import.csv, D/name_flags.tsv.
Headers use Apollo's 'Custom Field: <label>' convention (labels must match apollo_fields_index; check first).
Honest fallback when there is no validated hook: opener says WHY we are writing, never that we 'read' something.
"""
import argparse, csv, hashlib, html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import AREA, BR, WL, COMPLIANCE_SENTENCE, clean_company, fix_workload_case

HEAVY_CC = "about 22 hours on an 8x A100 80GB node"
LIGHT_CC = "about 40 hours on a 4x L40 node"
# Spend sentence variants by funding stage: CONFIRM THESE WITH THE USER in Phase 0 (numbers are theirs, not ours).
SPEND = {
    "seed": "For reference, a typical seed-stage startup running GPUs on a hyperscaler pays around $8-20K a month, and even our list rates, without the startup discounts, would save $2.5-8K of that.",
    "later": "For reference, a Series A-B startup running GPUs on a hyperscaler often pays $50-200K a month, so even our list rates, without the startup discounts, could save $15-60K of that.",
    "unknown": "For reference, startups running GPUs on a hyperscaler often pay $8-200K a month depending on stage, and even our list rates, without the startup discounts, can save 30-40% of that ($2.4K-$80K saved monthly).",
}
V1 = "I'm reaching out to {c} because it looks like you're working on {a}."
V2 = "{c} came up as a team working on {a}, so I'm writing to you directly."
COLSOUT = ["contact email", "contact first name", "contact last name", "contact title", "account name",
           "Custom Field: Hi Greeting", "Custom Field: opener", "Custom Field: bridge", "Custom Field: workload",
           "Custom Field: credit_compute", "Custom Field: spend_sentence", "Custom Field: Source Website",
           "Custom Field: Enrichment flags", "Custom Field: Enrichment evidence", "Custom Field: funding_stage",
           "Custom Field: Last Round Amount", "Custom Field: Last Round Date", "Custom Field: Implied Valuation",
           "Custom Field: Funding Data Source URL", "apollo contact id"]  # last 4 funding columns after funding_stage may be NEW fields: flag to user
V_COLS = ["contact_id", "opener", "bridge", "workload", "wclass", "hook_grade", "source_url", "evidence", "ev",
          "d_loc", "d_hook", "d_compute", "d_status"]


def stage_bucket(stage):
    s = (stage or "").lower()
    if not s or s in ("unknown", "undisclosed"): return "unknown"
    if re.search(r"pre-?seed|seed|angel|accelerator|grant", s): return "seed"
    return "later"


def flags(r, grade):
    p = []
    for k, lab in (("d_loc", "DUBIOUS-LOCATION"), ("d_hook", "DUBIOUS-HOOK"), ("d_compute", "DUBIOUS-COMPUTE"), ("d_status", "DUBIOUS-STARTUP-STATUS")):
        v = r.get(k, "")
        if v and v != "none": p.append(f"{lab}: {v}")
    if grade not in ("P", "F") and not any(x.startswith("DUBIOUS-HOOK") for x in p):
        p.append("DUBIOUS-HOOK: company-level or scripted opener")
    return ". ".join(p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--funding"); ap.add_argument("--include-unprocessed", action="store_true", help="also emit contacts that were never researched (fallback copy). Default: processed contacts only"); a = ap.parse_args()
    D = a.dir
    contacts = list(csv.DictReader(open(os.path.join(D, "contacts.tsv"), newline="", encoding="utf-8"), delimiter="\t"))
    val = {}
    p = os.path.join(D, "validated.tsv")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            f = (line.rstrip("\n").split("\t") + [""] * 13)[:13]
            val[f[0]] = dict(zip(V_COLS, f))
    fund = {}
    if a.funding and os.path.exists(a.funding):
        for r in csv.DictReader(open(a.funding, newline="", encoding="utf-8"), delimiter="\t"):
            fund[r["company_domain"].lower()] = r
    searched = set()
    rp = os.path.join(D, "research.tsv")
    if os.path.exists(rp):
        for line in open(rp, encoding="utf-8"):
            searched.add(line.split("\t")[0])
    rows, nf, unproc = [], [], []
    for c in contacts:
        if c["contact_id"] not in searched and not a.include_unprocessed:
            unproc.append(c["contact_id"] + "\t" + c["email"] + "\t" + (c.get("bucket") or "")); continue
        r = val.get(c["contact_id"]); b = c.get("bucket") or "other_ai"
        co = clean_company(c["company"])
        if r:
            op, br, wl, cl, g = r["opener"], r["bridge"], r["workload"], r["wclass"], r["hook_grade"]
            url, ev, fl = r["source_url"], r["evidence"], flags(r, g)
        else:
            use1 = co[:1].islower() or int(hashlib.md5(c["contact_id"].encode()).hexdigest(), 16) % 2 == 0
            op = (V1 if use1 else V2).format(c=co, a=AREA.get(b, AREA["other_ai"]))
            br = BR.get(b, BR["other_ai"]) + (COMPLIANCE_SENTENCE if c.get("compliance") == "1" else "")
            wl, cl, url, ev, fl = WL.get(b, WL["other_ai"]), c.get("class", "light"), "", "", flags({}, "NONE")
        fn, ln = html.unescape(c["first"]).strip(), html.unescape(c["last"]).strip()
        if not re.fullmatch(r"[A-Z][a-z]{2,}(-[A-Z][a-z]+)?", fn) or not ln:
            nf.append((c["contact_id"], fn, ln, c["email"], "check name"))
        fd = fund.get((c.get("domain") or "").lower(), {})
        stage = fd.get("funding_stage", "")
        sp = SPEND[stage_bucket(stage)]
        sp += " By Series B the same bill is often $50-200K a month, so the savings grow to $15-60K, which is why switching early is easier than switching later." if stage_bucket(stage) == "seed" else ""
        rows.append({"contact email": c["email"], "contact first name": fn, "contact last name": ln,
                     "contact title": html.unescape(c["title"]), "account name": html.unescape(c["company"]),
                     "Custom Field: Hi Greeting": f"Hi {fn},", "Custom Field: opener": op, "Custom Field: bridge": br,
                     "Custom Field: workload": fix_workload_case(wl),
                     "Custom Field: credit_compute": HEAVY_CC if cl == "heavy" else LIGHT_CC,
                     "Custom Field: spend_sentence": sp, "Custom Field: Source Website": url,
                     "Custom Field: Enrichment flags": fl, "Custom Field: Enrichment evidence": ev,
                     "Custom Field: funding_stage": stage, "Custom Field: Last Round Amount": fd.get("last_round_amount_usd", ""),
                     "Custom Field: Last Round Date": fd.get("last_round_date", ""),
                     "Custom Field: Implied Valuation": fd.get("post_money_valuation_usd", ""),
                     "Custom Field: Funding Data Source URL": fd.get("source_url", ""), "apollo contact id": c["contact_id"]})
    cols = [k for k in COLSOUT if (fund or not k.startswith("Custom Field: Last Round") and k not in ("Custom Field: Implied Valuation", "Custom Field: Funding Data Source URL", "Custom Field: funding_stage"))]
    with open(os.path.join(D, "import.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    with open(os.path.join(D, "unprocessed.tsv"), "w", encoding="utf-8") as f:
        f.write("\n".join(unproc) + ("\n" if unproc else ""))
    with open(os.path.join(D, "name_flags.tsv"), "w", encoding="utf-8") as f:
        for t in nf: f.write("\t".join(t) + "\n")
    res = sum(1 for c in contacts if c["contact_id"] in val)
    print(f"import rows {len(rows)} validated-hook {res} searched-but-fallback-copy {len(rows)-res} UNPROCESSED-excluded {len(unproc)} name_flags {len(nf)} funding_rows {len(fund)}")
