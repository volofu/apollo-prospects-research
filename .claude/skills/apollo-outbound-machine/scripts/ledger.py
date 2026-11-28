"""Contact ledger: the single source of truth that prevents redundant research after usage outages.
usage:
  ledger.py init    --dir D --contacts contacts.tsv
  ledger.py batches --dir D [--size N|auto] [--max N] [--reclaim]
  ledger.py merge   --dir D
  ledger.py status  --dir D
contacts.tsv header (tab separated): contact_id first last title company domain email bucket class compliance
  bucket in robotics_vision|llm_agents|bio_health|video_media|data_ml_infra|other_ai ; class heavy|light ; compliance 0|1
Files in D: contacts.tsv, batches/bNNNN.tsv, out/bNNNN.tsv (workers append), research.tsv (merged, deduped),
  claims.tsv (batch,contact_id,claimed_at), state.json
Rules: a contact is DONE once any out/*.tsv holds a well-formed 19-column row for it with a real search result.
  Batches are always rebuilt from NOT-DONE contacts, so a half-finished batch is re-packed, never rerun whole.
"""
import argparse, csv, glob, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FOCUS, clean_company

COLS = ["contact_id", "opener", "bridge", "workload", "wclass", "hook_grade", "source_url", "evidence", "ev",
        "d_loc", "d_hook", "d_compute", "d_status", "variant", "playbook_ver", "searches", "fetches", "src_type",
        "class_src_url"]
ERR = ("too_many_requests", "budget used up", "rate limit", "rate_limit", "search failed", "tool error")
CLAIM_TTL = 50 * 60


def load_contacts(d):
    with open(os.path.join(d, "contacts.tsv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_out(d):
    """Return {contact_id: row} (last good row wins) and count of bad lines."""
    good, bad = {}, 0
    for p in sorted(glob.glob(os.path.join(d, "out", "b*.tsv"))):
        for line in open(p, encoding="utf-8", errors="replace"):
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 19:
                bad += 1
                continue
            blob = " ".join(f[7:13]).lower()
            if any(e in blob for e in ERR):  # a failed search must never count as done
                bad += 1
                continue
            good[f[0]] = f
    return good, bad


def read_done(d, contacts):
    ids = {c["contact_id"] for c in contacts}
    good, bad = read_out(d)
    return {k: v for k, v in good.items() if k in ids}, bad


def state_path(d):
    return os.path.join(d, "state.json")


def load_state(d):
    try:
        return json.load(open(state_path(d)))
    except Exception:
        return {"next_batch": 0, "size": 10, "history": []}


def save_state(d, s):
    json.dump(s, open(state_path(d), "w"), indent=1)


def read_claims(d):
    p = os.path.join(d, "claims.tsv")
    out = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            f = line.rstrip("\n").split("\t")
            if len(f) == 3:
                out.append((f[0], f[1], float(f[2])))
    return out


def cmd_init(a):
    os.makedirs(os.path.join(a.dir, "batches"), exist_ok=True)
    os.makedirs(os.path.join(a.dir, "out"), exist_ok=True)
    if os.path.abspath(a.contacts) != os.path.abspath(os.path.join(a.dir, "contacts.tsv")):
        open(os.path.join(a.dir, "contacts.tsv"), "w", encoding="utf-8").write(open(a.contacts, encoding="utf-8").read())
    n = len(load_contacts(a.dir))
    save_state(a.dir, load_state(a.dir))
    print(f"contacts {n}")


def cmd_batches(a):
    st = load_state(a.dir)
    size = st.get("size", 10) if a.size == "auto" else int(a.size)
    contacts = load_contacts(a.dir)
    done, _ = read_done(a.dir, contacts)
    now = time.time()
    claims = read_claims(a.dir)
    live = {c for _, c, t in claims if (now - t) < CLAIM_TTL} if not a.reclaim else set()
    pending = [c for c in contacts if c["contact_id"] not in done and c["contact_id"] not in live]
    if a.max:
        pending = pending[: a.max]
    made = []
    with open(os.path.join(a.dir, "claims.tsv"), "a", encoding="utf-8") as cf:
        for i in range(0, len(pending), size):
            chunk = pending[i:i + size]
            n = st["next_batch"]
            st["next_batch"] = n + 1
            bid = f"b{n:04d}"
            outp = os.path.abspath(os.path.join(a.dir, "out", bid + ".tsv"))
            with open(os.path.join(a.dir, "batches", bid + ".tsv"), "w", encoding="utf-8") as f:
                f.write(f"#OUT_FILE\t{outp}\tv1\t{bid}\n")
                for r in chunk:
                    comp = clean_company(r["company"])
                    focus = FOCUS.get(r.get("bucket", ""), "AI")
                    who = f'{r["first"]} {r["last"]}'.strip()
                    q = f'"{comp}" {focus} {who} (launch OR interview OR blog OR paper OR podcast) -site:linkedin.com'
                    f.write("\t".join([r["contact_id"], str(i), r["first"], r["last"], r["title"], comp,
                                       r.get("bucket", "other_ai"), r.get("class", "light"),
                                       r.get("compliance", "0"), "a", q]) + "\n")
                    cf.write(f'{bid}\t{r["contact_id"]}\t{now}\n')
            made.append(os.path.abspath(os.path.join(a.dir, "batches", bid + ".tsv")))
    save_state(a.dir, st)
    print(f"pending {len(pending)} size {size} -> {len(made)} new batches")
    for m in made:
        print(m)


def cmd_merge(a):
    contacts = load_contacts(a.dir)
    done, bad = read_done(a.dir, contacts)
    with open(os.path.join(a.dir, "research.tsv"), "w", encoding="utf-8") as f:
        for c in contacts:
            if c["contact_id"] in done:
                f.write("\t".join(done[c["contact_id"]]) + "\n")
    st = load_state(a.dir)
    # completion rate per claimed batch whose worker has stopped writing (claim older than 2 minutes)
    claims = read_claims(a.dir)
    now = time.time()
    per = {}
    for b, cid, t in claims:
        if now - t > 120:
            per.setdefault(b, [0, 0])
            per[b][0] += 1
            per[b][1] += 1 if cid in done else 0
    # only count batches from the most recent wave (last 20)
    recent = list(per.items())[-20:]
    assigned = sum(v[0] for _, v in recent)
    got = sum(v[1] for _, v in recent)
    rate = got / assigned if assigned else 1.0
    rec = st.get("size", 10)
    if assigned >= 30 and rate < 0.95:
        rec = max(6, int(rec * max(rate, 0.6)))
    elif assigned >= 30 and rate >= 0.99 and rec < 20:
        rec = min(20, rec + 2)
    st["size"] = rec
    st["history"].append({"t": now, "done": len(done), "pending": len(contacts) - len(done), "rate": round(rate, 3)})
    save_state(a.dir, st)
    print(f"done {len(done)}/{len(contacts)} pending {len(contacts)-len(done)} bad_lines_ignored {bad} "
          f"recent_completion {rate:.0%} recommended_batch_size {rec}")


def cmd_status(a):
    contacts = load_contacts(a.dir)
    done, bad = read_done(a.dir, contacts)
    st = load_state(a.dir)
    hooks = sum(1 for r in done.values() if r[5] in ("P", "F"))
    print(f"contacts {len(contacts)} done {len(done)} pending {len(contacts)-len(done)} P/F hooks {hooks} "
          f"batch_size {st.get('size')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "batches", "merge", "status"):
        p = sp.add_parser(name)
        p.add_argument("--dir", required=True)
        if name == "init":
            p.add_argument("--contacts", required=True)
        if name == "batches":
            p.add_argument("--size", default="auto")
            p.add_argument("--max", type=int, default=0)
            p.add_argument("--reclaim", action="store_true")
    a = ap.parse_args()
    {"init": cmd_init, "batches": cmd_batches, "merge": cmd_merge, "status": cmd_status}[a.cmd](a)
