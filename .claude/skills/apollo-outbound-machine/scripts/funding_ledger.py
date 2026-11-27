"""Company-level funding research ledger (one row per company domain, not per contact).
usage: funding_ledger.py batches --dir D [--size 10] [--reclaim]   (builds D/fbatches/fNNNN.tsv from companies not yet done)
       funding_ledger.py merge   --dir D                           (D/fout/f*.tsv -> D/funding.tsv with header; prints coverage)
Reads D/contacts.tsv. Workers append 11-column rows to D/fout/fNNNN.tsv (see funding_prompt.md).
Skip companies Apollo already answered: put them in D/funding_apollo.tsv (same header as funding.tsv) first.
"""
import argparse, csv, glob, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import clean_company
H = ["company_domain", "funding_stage", "last_round_amount_usd", "last_round_date", "total_funding_usd",
     "post_money_valuation_usd", "valuation_basis", "source_url", "confidence", "evidence", "notes"]
ERR = ("too_many_requests", "budget used up", "rate limit", "rate_limit")
TTL = 50 * 60


def companies(d):
    seen = {}
    for r in csv.DictReader(open(os.path.join(d, "contacts.tsv"), newline="", encoding="utf-8"), delimiter="\t"):
        dom = (r.get("domain") or "").lower().strip()
        if dom and dom not in seen: seen[dom] = (clean_company(r["company"]), r.get("bucket", "other_ai"))
    return seen


def done_rows(d):
    rows = {}
    for p in sorted(glob.glob(os.path.join(d, "fout", "f*.tsv"))) + [os.path.join(d, "funding_apollo.tsv")]:
        if not os.path.exists(p): continue
        for line in open(p, encoding="utf-8", errors="replace"):
            if not line.strip() or line.startswith("#") or line.startswith("company_domain"): continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 11 or any(e in line.lower() for e in ERR): continue
            rows[f[0].lower()] = f
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("batches", "merge"):
        p = sp.add_parser(n); p.add_argument("--dir", required=True)
        if n == "batches": p.add_argument("--size", type=int, default=10); p.add_argument("--reclaim", action="store_true")
    a = ap.parse_args(); D = a.dir
    comp = companies(D); done = done_rows(D)
    if a.cmd == "batches":
        os.makedirs(os.path.join(D, "fbatches"), exist_ok=True); os.makedirs(os.path.join(D, "fout"), exist_ok=True)
        cp = os.path.join(D, "fclaims.tsv"); now = time.time(); live = set()
        if os.path.exists(cp) and not a.reclaim:
            for l in open(cp, encoding="utf-8"):
                x = l.split("\t")
                if len(x) == 2 and now - float(x[1]) < TTL: live.add(x[0])
        pend = [(k, v) for k, v in comp.items() if k not in done and k not in live]
        n0 = len(glob.glob(os.path.join(D, "fbatches", "f*.tsv"))); made = []
        with open(cp, "a", encoding="utf-8") as cf:
            for i in range(0, len(pend), a.size):
                bid = f"f{n0 + i // a.size:04d}"; out = os.path.abspath(os.path.join(D, "fout", bid + ".tsv"))
                with open(os.path.join(D, "fbatches", bid + ".tsv"), "w", encoding="utf-8") as f:
                    f.write(f"#OUT_FILE\t{out}\tv1\t{bid}\n")
                    for k, (name, b) in pend[i:i + a.size]:
                        f.write(f"{k}\t{name}\t{b}\n"); cf.write(f"{k}\t{now}\n")
                made.append(os.path.abspath(os.path.join(D, "fbatches", bid + ".tsv")))
        print(f"companies {len(comp)} done {len(done)} pending {len(pend)} -> {len(made)} batches"); print("\n".join(made))
    else:
        with open(os.path.join(D, "funding.tsv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter="\t"); w.writerow(H)
            for k in comp:
                if k in done: w.writerow(done[k])
        have = sum(1 for k in comp if k in done); amt = sum(1 for k in comp if k in done and done[k][2])
        val = sum(1 for k in comp if k in done and done[k][5])
        print(f"funding rows {have}/{len(comp)} with round amount {amt} with valuation {val} (valuation is often undisclosed)")
