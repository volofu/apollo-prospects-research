"""Print the next batch file path and assign a search-query variant per contact (continuous improvement).
usage: python -I next_batch.py --dir <working folder> --n 8
Reads queue.csv, out/*.tsv (done), batches/*.tsv (assigned), optional variant_stats.json and playbook_ver.txt.
Variant policy per bucket: until every variant has MIN_N samples, give the least-sampled variant (explore);
afterwards 80% the best-scoring variant, 20% a random other (keeps exploring). Deterministic per contact id.
Batch file: line 1 '#OUT_FILE<TAB>path<TAB>playbook_ver<TAB>batch_id', then rows:
contact_id, rank, first, last, title, company, bucket, class, compliance, variant, query
"""
import argparse, csv, glob, json, os, random, time

MIN_N = 30
VARIANTS = ["a", "b", "c"]
ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--n", type=int, default=8)
a = ap.parse_args()
os.makedirs(os.path.join(a.dir, "batches"), exist_ok=True)
os.makedirs(os.path.join(a.dir, "out"), exist_ok=True)
done = set()
for p in glob.glob(os.path.join(a.dir, "out", "*.tsv")) + glob.glob(os.path.join(a.dir, "batches", "*.tsv")):
    for r in csv.reader(open(p, encoding="utf-8"), delimiter="\t"):
        if r and not r[0].startswith("#"):
            done.add(r[0])
rows = [r for r in csv.DictReader(open(os.path.join(a.dir, "queue.csv"), newline="", encoding="utf-8"))
        if r["hold"] == "0" and r["contact_id"] not in done]
rows.sort(key=lambda r: float(r["rank"]))
rows = rows[: a.n]
if not rows:
    print("EMPTY")
    raise SystemExit
stats = {}
sp = os.path.join(a.dir, "variant_stats.json")
if os.path.exists(sp):
    stats = json.load(open(sp, encoding="utf-8"))
pv = "v1"
pp = os.path.join(a.dir, "playbook_ver.txt")
if os.path.exists(pp):
    pv = open(pp, encoding="utf-8").read().strip() or "v1"


def pick(r):
    st = stats.get(r["bucket"], {})
    ns = {v: st.get(v, {}).get("n", 0) for v in VARIANTS}
    if min(ns.values()) < MIN_N:
        return min(VARIANTS, key=lambda v: (ns[v], v))
    rnd = random.Random(r["contact_id"])
    best = max(VARIANTS, key=lambda v: st[v].get("score", 0))
    if rnd.random() < 0.8:
        return best
    return rnd.choice([v for v in VARIANTS if v != best])


ts = time.strftime("%Y%m%d_%H%M%S") + f"_{rows[0]['rank']}"
bid = ts
bp = os.path.join(a.dir, "batches", f"batch_{ts}.tsv")
op = os.path.join(a.dir, "out", f"out_{ts}.tsv")
with open(bp, "w", newline="", encoding="utf-8") as f:
    f.write(f"#OUT_FILE\t{op}\t{pv}\t{bid}\n")
    w = csv.writer(f, delimiter="\t")
    for r in rows:
        v = pick(r)
        w.writerow([r["contact_id"], r["rank"], r["first"], r["last"], r["title"], r["company"],
                    r["bucket"], r["class"], r["compliance"], v, r["query_" + v]])
print(bp)
