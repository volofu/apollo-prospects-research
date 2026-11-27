"""Render every sequence email with real merge data and flag problems. No LLM.
usage: render_check.py --templates templates.json --csv import.csv [--samples 6] [--seed 1]
templates.json: [{"step":1,"variant":"A","subject":"...","body_html":"<p>..</p>"}, ...]  (from apollo_emailer_campaigns_show)
Placeholders: {{first_name}} -> 'contact first name' column; {{contact.<field>}} -> 'Custom Field: <field>' (case/space/underscore-insensitive);
{{account.name}} -> 'account name'.  Exit code 1 if any hard problem.
"""
import argparse, collections, csv, html, json, random, re, sys

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

def html_to_text(h):
    h = re.sub(r"</p>\s*<p>", "\n\n", h); h = re.sub(r"<br\s*/?>", "\n", h); h = re.sub(r"<[^>]+>", "", h)
    return html.unescape(h).strip()

def render(t, row):
    cf = {norm(k.replace("Custom Field:", "")): v for k, v in row.items() if k.startswith("Custom Field:")}
    def sub(m):
        key = m.group(1).strip()
        if key == "first_name": return row["contact first name"]
        if key == "last_name": return row["contact last name"]
        if key in ("account.name", "company"): return row["account name"]
        if key.startswith("contact."): return cf.get(norm(key[8:]), "\x00MISSING:" + key)
        return "\x00MISSING:" + key
    return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", sub, t)

PROBLEMS = [
    (r"\x00MISSING:[^\s.,]*", "unfilled or unknown merge field"),
    (r"  +", "double space"), (r"\.\.(?!\.)", "double period"), (r"\s,|,,", "stray comma"),
    (r"(?m)^[a-z]", "line starts lowercase"), (r"\bI (read|saw|heard) about\b", "claims reading unverified 'about' (fallback-style opener)"),
    (r"(?i)\bwork on (LLM|robotics|ML infrastructure|generative video|biotech AI),", "legacy fallback 'work on X,' phrasing"),
]
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--templates", required=True); ap.add_argument("--csv", required=True)
    ap.add_argument("--samples", type=int, default=6); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    T = json.load(open(a.templates, encoding="utf-8"))
    rows = list(csv.DictReader(open(a.csv, newline="", encoding="utf-8")))
    used = set()
    for t in T: used |= set(re.findall(r"\{\{\s*contact\.([^}]+?)\s*\}\}", t["body_html"] + t.get("subject", "")))
    have = {norm(k.replace("Custom Field:", "")) for k in rows[0] if k.startswith("Custom Field:")}
    miss = [u for u in used if norm(u) not in have]
    print("merge fields used by templates:", sorted(used))
    if miss: print("HARD: template uses fields with no CSV column:", miss)
    bad = collections.Counter(); ex = {}
    for r in rows:
        for t in T:
            txt = render(html_to_text(t["body_html"]), r)
            for rx, name in PROBLEMS:
                if re.search(rx, txt): bad[(f'{t["step"]}{t["variant"]}', name)] += 1; ex.setdefault((f'{t["step"]}{t["variant"]}', name), r["account name"])
        for k in ("Custom Field: opener", "Custom Field: bridge"):
            if r[k] and r[k].strip()[-1] not in ".!?": bad[(k, "no end punctuation")] += 1
    print("problems:", dict(bad) or "none"); print("examples:", ex)
    random.seed(a.seed)
    fb = [r for r in rows if not r["Custom Field: Source Website"]]; rs = [r for r in rows if r["Custom Field: Source Website"]]
    pick = random.sample(rs, min(a.samples // 2, len(rs))) + random.sample(fb, min(a.samples - a.samples // 2, len(fb)))
    for r in pick:
        print("=" * 72, r["account name"], "| researched" if r["Custom Field: Source Website"] else "| fallback")
        for t in T:
            if t["step"] == 1 and t["variant"] in ("A", "C") or (t["step"] > 1 and t["variant"] == "A" and r is pick[0]):
                print(f'--- step {t["step"]}{t["variant"]}'); print(render(html_to_text(t["body_html"]), r))
    sys.exit(1 if (miss or any(k[1] in ("unfilled or unknown merge field", "double space", "double period") for k in bad)) else 0)
