"""Continuous-improvement retro. No LLM. Run every ~200 researched contacts (and weekly).
usage: python -I retro.py --dir <working folder> [--min-n 20]
Inputs in <dir>: validated.tsv, failed.tsv (from validate.py), queue.csv, optional usage.csv
usage.csv columns: batch_id, n_contacts, subagent_tokens, tool_uses, duration_ms, model, playbook_ver
Outputs: source_stats.csv (per domain), type_stats.csv (per src_type), variant_stats.json (per bucket x variant),
retro_report.md (promote / demote / explore suggestions). Token numbers per contact are ESTIMATES: each batch's
subagent tokens are split across its contacts in proportion to (searches + 1.5 x fetches).
"""
import argparse, collections, csv, json, os
from urllib.parse import urlparse

OUT = ["contact_id", "opener", "bridge", "workload", "wclass", "hook_grade", "source_url", "evidence", "ev",
       "d_loc", "d_hook", "d_compute", "d_status", "variant", "playbook_ver", "searches", "fetches", "src_type",
       "class_src_url", "batch_id", "src_domain"]


def dom(u):
    h = urlparse(u).netloc.lower() if u else ""
    return h[4:] if h.startswith("www.") else h


def load(path, valid):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in csv.reader(open(path, encoding="utf-8"), delimiter="\t"):
        if not line:
            continue
        r = dict(zip(OUT, (line + [""] * len(OUT))[: len(OUT)]))
        r["valid"] = valid
        r["reason"] = "" if valid else (line[len(OUT)] if len(line) > len(OUT) else "")
        rows.append(r)
    return rows


def num(x, d=1.0):
    try:
        return float(x)
    except Exception:
        return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--min-n", type=int, default=20)
    a = ap.parse_args()
    rows = load(os.path.join(a.dir, "validated.tsv"), True) + load(os.path.join(a.dir, "failed.tsv"), False)
    bucket = {}
    qp = os.path.join(a.dir, "queue.csv")
    if os.path.exists(qp):
        for r in csv.DictReader(open(qp, newline="", encoding="utf-8")):
            bucket[r["contact_id"]] = r["bucket"]
    usage = {}
    up = os.path.join(a.dir, "usage.csv")
    if os.path.exists(up):
        for r in csv.DictReader(open(up, newline="", encoding="utf-8")):
            usage[r["batch_id"]] = r
    # allocate tokens
    by_batch = collections.defaultdict(list)
    for r in rows:
        w = max(num(r["searches"], 1) + 1.5 * num(r["fetches"], 0), 1.0)
        r["w"] = w
        by_batch[r["batch_id"]].append(r)
    for bid, rs in by_batch.items():
        tot_w = sum(r["w"] for r in rs)
        tok = num(usage.get(bid, {}).get("subagent_tokens", ""), 0)
        for r in rs:
            r["tok"] = tok * r["w"] / tot_w if tok else 0.0
    pf = lambda r: r["valid"] and r["hook_grade"] in ("P", "F")

    def agg(keyfn):
        d = collections.defaultdict(lambda: {"n": 0, "valid": 0, "pf": 0, "tok": 0.0})
        for r in rows:
            k = keyfn(r)
            if not k:
                continue
            x = d[k]
            x["n"] += 1
            x["valid"] += 1 if r["valid"] else 0
            x["pf"] += 1 if pf(r) else 0
            x["tok"] += r["tok"]
        return d

    def write(path, d, label):
        with open(os.path.join(a.dir, path), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([label, "n", "valid", "valid_pf_hooks", "pf_rate", "est_tokens", "tokens_per_pf_hook"])
            for k, x in sorted(d.items(), key=lambda kv: -kv[1]["pf"]):
                w.writerow([k, x["n"], x["valid"], x["pf"], round(x["pf"] / x["n"], 3), int(x["tok"]),
                            int(x["tok"] / x["pf"]) if x["pf"] and x["tok"] else ""])

    dd = agg(lambda r: r["src_domain"])
    tt = agg(lambda r: r["src_type"])
    write("source_stats.csv", dd, "domain")
    write("type_stats.csv", tt, "src_type")
    vs = collections.defaultdict(dict)
    vx = agg(lambda r: (bucket.get(r["contact_id"], "?") + "|" + (r["variant"] or "a")))
    for k, x in vx.items():
        b, v = k.split("|")
        eff = x["pf"] * 10000 / x["tok"] if x["tok"] else None
        rate = x["pf"] / x["n"]
        vs[b][v] = {"n": x["n"], "pf_rate": round(rate, 3), "pf_per_10k_tokens": round(eff, 2) if eff else None,
                    "score": round(eff if eff else rate, 3)}
    json.dump(vs, open(os.path.join(a.dir, "variant_stats.json"), "w", encoding="utf-8"), indent=1)
    lines = ["# Retro report", f"rows analysed: {len(rows)} (valid {sum(r['valid'] for r in rows)})", ""]
    reliable = {k: x for k, x in dd.items() if x["n"] >= a.min_n}
    lines.append(f"## Domains with n >= {a.min_n} (promote / demote candidates)")
    for k, x in sorted(reliable.items(), key=lambda kv: -kv[1]["pf"] / kv[1]["n"]):
        rate = x["pf"] / x["n"]
        tag = "PROMOTE" if rate >= 0.6 else ("DEMOTE" if rate < 0.25 else "keep")
        lines.append(f"- {k}: n={x['n']}, P/F hook rate {rate:.0%}, est tokens/hook {int(x['tok']/x['pf']) if x['pf'] and x['tok'] else 'n/a'} -> {tag}")
    if not reliable:
        lines.append("- none yet; keep exploring (no domain has enough samples).")
    lines.append("")
    lines.append("## Bucket x variant (a=baseline keywords, b=site-targeted, c=compute/careers)")
    for b, vv in vs.items():
        lines.append(f"- {b}: " + "; ".join(f"{v}: n={s['n']} pf_rate={s['pf_rate']}" for v, s in sorted(vv.items())))
    fails = collections.Counter(r["reason"].split(";")[0] for r in rows if not r["valid"])
    lines.append("")
    lines.append("## Top validation failures: " + ", ".join(f"{k} ({n})" for k, n in fails.most_common(5)))
    lines.append("")
    lines.append("Rules for editing the playbook: change at most 3 things per retro; need n >= min-n before promoting or demoting a domain; "
                 "keep 20% exploration; bump playbook_ver (v2, v3...).")
    open(os.path.join(a.dir, "retro_report.md"), "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
