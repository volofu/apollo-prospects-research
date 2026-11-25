"""Build queue.csv from an Apollo list export (CSV). No LLM, no network.
usage: python -I prep_queue.py --export export.csv [--ranks ranks.csv] --out queue.csv
ranks.csv: columns contact_id,rank (lower is better). Without it, file order is the rank.
"""
import argparse, csv, math, re, collections

STOP = set("""b2b b2c saas services information technology & services enterprise software enterprises computer software
consumer internet consumers internet technology, information & internet software development
research and development in the physical, engineering, and life sciences
artificial intelligence machine learning ai data analytics analytics""".split("\n"))
STOP_WORDS = {w.strip() for line in STOP for w in line.split(",") if w.strip()}
STOP_WORDS |= {"b2b", "b2c", "saas", "services", "ai", "artificial intelligence", "machine learning", "enterprise",
               "enterprises", "computer software", "information technology & services", "internet", "consumers",
               "consumer internet", "enterprise software", "software development", "automation", "technology",
               "information & internet", "technology, information & internet", "data analytics", "analytics",
               "research", "healthcare", "manufacturing", "retail", "government", "distribution"}

BUCKETS = [
    ("bio_health", r"protein|genom|omics|antibod|biotech|drug|clinical|patient|pharma|medical|health|cell |crispr|molecul|diagnos"),
    ("video_media", r"video|audio|music|image generation|diffusion|generative media|film|avatar|speech|voice"),
    ("robotics_vision", r"robot|drone|autonom|computer vision|lidar|perception|navigation|vision|sensor|slam"),
    ("llm_agents", r"llm|language model|agent|chatbot|rag|prompt|copilot|nlp|foundation model|genai|generative"),
    ("data_ml_infra", r"mlops|gpu|inference|training|infrastructure|data platform|vector|model deployment|compute"),
]
HEAVY_RE = r"foundation model|pretrain|pre-train|world model|large language model|video generation|diffusion|multi-node|reinforcement learning"
COMPLIANCE_RE = r"clinical|patient|hipaa|medical|healthcare|health care|ehr|biobank|genom"
WL = {
    "bio_health": "protein and omics model runs",
    "video_media": "video and audio model training",
    "robotics_vision": "perception model retraining",
    "llm_agents": "fine-tuning and eval runs",
    "data_ml_infra": "training and eval runs",
    "other_ai": "GPU training and eval runs",
}
BR = {
    "bio_health": "I'd guess model runs on new experimental batches come in bursts, which is where flexible GPU capacity helps.",
    "video_media": "I'd guess training and fine-tuning generation models comes in bursts around each release, which is where flexible capacity helps.",
    "robotics_vision": "I'd guess perception and policy models get retrained and evaluated in bursts as new data arrives, which is where flexible GPU capacity helps.",
    "llm_agents": "I'd guess fine-tunes and eval sweeps come in bursts around each release, which is where flexible capacity helps.",
    "data_ml_infra": "I'd guess training and eval jobs come in bursts around each experiment cycle, which is where flexible capacity helps.",
    "other_ai": "I'd guess training and eval runs come in bursts around each release, which is where flexible capacity helps.",
}
COMPLIANCE_SENTENCE = " We'd keep it to synthetic or de-identified data, since we're not a HIPAA environment."
# Seed source playbook v1: preferred domains per bucket (the retro step rewrites this over time via --playbook)
DOMAINS = {
    "robotics_vision": ["ycombinator.com", "techcrunch.com", "github.com", "arxiv.org", "therobotreport.com"],
    "llm_agents": ["ycombinator.com", "github.com", "huggingface.co", "techcrunch.com", "venturebeat.com"],
    "bio_health": ["pubmed.ncbi.nlm.nih.gov", "biorxiv.org", "fiercebiotech.com", "endpts.com", "businesswire.com"],
    "video_media": ["ycombinator.com", "arxiv.org", "huggingface.co", "techcrunch.com", "producthunt.com"],
    "data_ml_infra": ["github.com", "huggingface.co", "ycombinator.com", "venturebeat.com", "infoq.com"],
    "other_ai": ["ycombinator.com", "techcrunch.com", "github.com", "venturebeat.com", "prnewswire.com"],
}


def kws(row):
    raw = row.get("Keywords", "") or ""
    out = []
    for k in [x.strip().lower() for x in raw.split(",")]:
        if k and k not in STOP_WORDS and 3 <= len(k) <= 40 and k not in out:
            out.append(k)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--ranks")
    ap.add_argument("--out", required=True)
    ap.add_argument("--playbook", help="optional json {bucket: [domains]} overriding the seed playbook")
    a = ap.parse_args()
    ranks = {}
    dom = dict(DOMAINS)
    if a.playbook:
        import json
        dom.update(json.load(open(a.playbook)))
    if a.ranks:
        for r in csv.DictReader(open(a.ranks, newline="", encoding="utf-8-sig")):
            ranks[r["contact_id"]] = float(r["rank"])
    rows = [r for r in csv.DictReader(open(a.export, newline="", encoding="utf-8-sig"))
            if (r.get("Email Status", "").strip().lower() == "verified") and r.get("Email", "").strip()]
    df = collections.Counter()
    for r in rows:
        for k in set(kws(r)):
            df[k] += 1
    n = max(len(rows), 1)
    for i, r in enumerate(rows):
        cid = r.get("Apollo Contact Id", "")
        r["_rank"] = ranks.get(cid, float(i + 1))
    rows.sort(key=lambda r: r["_rank"])
    seen_company = set()
    out = []
    for r in rows:
        ks = sorted(kws(r), key=lambda k: -math.log(n / (1 + df[k])))
        focus = []
        for k in ks:
            if not any(k in f or f in k for f in focus):
                focus.append(k)
            if len(focus) == 3:
                break
        blob = " ".join([r.get("Keywords", ""), r.get("Industry", ""), r.get("Technologies", "")]).lower()
        bucket = next((b for b, rx in BUCKETS if re.search(rx, blob)), "other_ai")
        heavy = bool(re.search(HEAVY_RE, blob))
        comp = bool(re.search(COMPLIANCE_RE, blob)) or bucket == "bio_health"
        company = (r.get("Company Name for Emails") or r.get("Company Name", "")).strip()
        domain = re.sub(r"^https?://(www\.)?", "", r.get("Website", "")).strip("/")
        hold = 1 if company.lower() in seen_company else 0
        seen_company.add(company.lower())
        f1 = focus[0] if focus else (r.get("Industry", "") or "AI").lower()
        f2 = focus[1] if len(focus) > 1 else ""
        who = f"{r.get('First Name','')} {r.get('Last Name','')}".strip()
        query = f'"{company}" {f1} {f2} {who} (launch OR interview OR blog OR paper OR podcast) -site:linkedin.com'.replace("  ", " ")
        sites = " OR ".join("site:" + d for d in dom[bucket][:4])
        query_b = f'"{company}" {who} ({sites})'.replace("  ", " ")
        query_c = f'"{company}" {f1} (careers OR hiring OR GPU OR PyTorch OR CUDA OR training OR "fine-tuning") -site:linkedin.com'.replace("  ", " ")
        if f2:
            fb_open = f"I read about {company}'s work on {f1} and {f2}, which is why I'm writing to you directly."
        else:
            fb_open = f"I read about {company}'s work on {f1}, which is why I'm reaching out to you directly about it."
        out.append({
            "rank": int(r["_rank"]) if float(r["_rank"]).is_integer() else r["_rank"],
            "contact_id": r.get("Apollo Contact Id", ""), "email": r["Email"].strip(),
            "first": r.get("First Name", ""), "last": r.get("Last Name", ""), "title": r.get("Title", ""),
            "company": company, "domain": domain, "focus": "|".join(focus), "bucket": bucket,
            "class": "heavy" if heavy else "light", "compliance": int(comp), "hold": hold,
            "search_query": query, "query_a": query, "query_b": query_b, "query_c": query_c, "fb_opener": fb_open,
            "fb_bridge": BR[bucket] + (COMPLIANCE_SENTENCE if comp else ""), "fb_workload": WL[bucket],
        })
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["rank"])
        w.writeheader()
        w.writerows(out)
    print(f"queue rows: {len(out)} (verified only), leads: {sum(1 for o in out if not o['hold'])}, held siblings: {sum(o['hold'] for o in out)}")


if __name__ == "__main__":
    main()
