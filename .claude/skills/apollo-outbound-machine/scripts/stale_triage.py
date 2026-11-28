"""Company-level stale triage and Apollo funding-band merge. No LLM, no network. Pairs with FREE apollo_organizations_lookup calls.
usage:
  stale_triage.py chunk  --domains domains.txt --out DIR [--size 100]     split domains into chunk files for lookup calls
  stale_triage.py decide --domains domains.txt --old old.txt --funded funded.txt --out stale.tsv [--cutoff 2020] [--dated dated.txt]
        old.txt    = domains returned by lookup with organization_founded_year_range {max: cutoff}
        funded.txt = domains returned by lookup with total_funding_range {min: 1}
        dated.txt  = (optional) domains returned by lookup with organization_founded_year_range {min: 1900}: founded year KNOWN.
        STALE = founded <= cutoff AND no funding in Apollo. Unknown founded year is never stale (reported separately).
  stale_triage.py bands  --domains domains.txt --bands DIR --out funding_apollo.tsv
        DIR holds files of returned domains, one per band: amt_<lo>_<hi>.txt (latest_funding_amount_range), date_<YYYYMMDD>_<YYYYMMDD>.txt
        (latest_funding_date_range). Writes the 11-column funding row with RANGE strings in amount/date and an inferred stage.
"""
import argparse, glob, os, re

STAGE_BY_MAX = [(2_000_000, "seed"), (6_000_000, "seed"), (20_000_000, "series-a"), (50_000_000, "series-b"), (10**12, "series-c-plus")]


def read(p):
    return {l.strip().lower() for l in open(p, encoding="utf-8") if l.strip()} if os.path.exists(p) else set()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("chunk"); c.add_argument("--domains", required=True); c.add_argument("--out", required=True); c.add_argument("--size", type=int, default=100)
    d = sp.add_parser("decide")
    for k in ("--domains", "--old", "--funded", "--out"): d.add_argument(k, required=True)
    d.add_argument("--cutoff", type=int, default=2020); d.add_argument("--dated")
    b = sp.add_parser("bands")
    for k in ("--domains", "--bands", "--out"): b.add_argument(k, required=True)
    a = ap.parse_args()
    dom = [x.strip().lower() for x in open(a.domains, encoding="utf-8") if x.strip()]
    if a.cmd == "chunk":
        os.makedirs(a.out, exist_ok=True)
        for i in range(0, len(dom), a.size):
            open(os.path.join(a.out, f"chunk{i // a.size:03d}.json"), "w").write('["' + '", "'.join(dom[i:i + a.size]) + '"]')
        print(f"{len(dom)} domains -> {(len(dom) + a.size - 1) // a.size} chunk files (paste each as q_organization_domains_list; per_page {a.size})")
    elif a.cmd == "decide":
        old, funded = read(a.old), read(a.funded); dated = read(a.dated) if a.dated else None
        stale = [x for x in dom if x in old and x not in funded]
        nodate = [x for x in dom if dated is not None and x not in dated]
        open(a.out, "w", encoding="utf-8").write("\n".join(stale) + ("\n" if stale else ""))
        print(f"domains {len(dom)} founded<={a.cutoff} {len([x for x in dom if x in old])} with Apollo funding {len([x for x in dom if x in funded])} STALE {len(stale)} founded-year-unknown (kept) {len(nodate)}")
    else:
        amt, dt = {}, {}
        for p in glob.glob(os.path.join(a.bands, "amt_*.txt")):
            m = re.match(r"amt_(\d+)_(\d+)\.txt", os.path.basename(p))
            for x in read(p): amt[x] = (int(m.group(1)), int(m.group(2)))
        for p in glob.glob(os.path.join(a.bands, "date_*.txt")):
            m = re.match(r"date_(\d{8})_(\d{8})\.txt", os.path.basename(p))
            for x in read(p): dt[x] = (m.group(1), m.group(2))
        n = 0
        with open(a.out, "w", encoding="utf-8") as f:
            for x in dom:
                if x not in amt and x not in dt: continue
                lo_hi = amt.get(x); dd = dt.get(x)
                stage = next((s for mx, s in STAGE_BY_MAX if lo_hi and lo_hi[1] <= mx), "unknown") if lo_hi else "unknown"
                ar = f"{lo_hi[0]}-{lo_hi[1]}" if lo_hi else ""
                dr = f"{dd[0][:4]}-{dd[0][4:6]}-{dd[0][6:]}..{dd[1][:4]}-{dd[1][4:6]}-{dd[1][6:]}" if dd else ""
                f.write("\t".join([x, stage, ar, dr, "", "", "undisclosed", "apollo-filter", "medium", "Apollo funding filter band, not an exact value", "stage inferred from amount band; range not exact"]) + "\n"); n += 1
        print(f"funding rows from Apollo bands: {n} of {len(dom)} (amounts and dates are RANGES; exact values and valuation need web research)")
