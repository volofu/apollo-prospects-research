# Runbook (Claude Code cloud session, repo checked out). Stop at every GATE.

Two kinds of cloud runs:
- **Interactive cloud session (claude.ai/code):** Jason is present. Steps 0-4 and 6-8 (anything that spends credits, writes to Apollo or enrolls).
- **Scheduled cloud routines:** unattended. Research only (Step 5). They never spend credits, enrich, enroll or send.

## Step 0: capabilities check
List what this session really has: Bash/Python, WebSearch/WebFetch, subagents, git, the Apollo connector, Google Sheets/Drive, Notion. Cloud has no local files and no Chrome, and probably no usage tool. Report what is missing and use the fallbacks below. If the Apollo or Google Sheets connector is missing, stop and tell Jason to connect it at claude.ai/customize/connectors (the session cannot do it).

## Step 1: size the real gap (free)
Ask Jason to read two numbers in the Apollo web app on "P1 Startups – People": verified emails, and how many of those are in no sequence. Eligible-existing = that second number minus held siblings and Jack/Pi. Gap = 3,500 minus eligible-existing. GATE: report the gap.

## Step 2: net-new candidate slices (free)
Apollo people search (free): US, 1-50 employees, pre-seed to Series A, AI/ML/robotics/bio-AI keywords, founder/co-founder/CEO/CTO, contact_email_status ["verified"], not already in my account. Size each slice with per_page 1. Plan about 1.4x the gap in candidates, one lead per company. GATE: slice table for Jason's approval.

## Step 2b: PRE-ENRICHMENT GATE (R0), free, public web only, before any credit is spent
Decided 2026-11-25: no email is revealed until the contact has been researched online. Candidates from Step 2 carry only first name, title, company and an obfuscated last name (Apollo masks it until enrichment), so research is keyed on company + first name + title. Research follows the R0 waterfall in the skill: (0) identify the exact company domain and LinkedIn company page, then (1) X-ray search of the person via web-search results only, (2) company website, (3) startup/tech directories (Crunchbase, YC, Wellfound, Product Hunt, GitHub org), (4) matching X profile; stop at the first step that confirms the current role. LinkedIn is read only through search-result titles/snippets, never opened. PitchBook skipped. Record per contact in the Master sheet tab `LR_Gate`: contact_id, status, still_there (yes/no/unknown), still_there_url, alive (yes/no/unknown), gpu_class (heavy/light/none/unknown), gpu_evidence (max 20 words), gpu_url, src_type, src_domain, checked_at.
- **PASS** = company is live (site, blog, press or job posts within about 12 months), a named person of that first name holds that role there (team page, founder-authored post, launch page, press), AND there is public evidence the work depends on GPU compute (training, fine-tuning, inference at scale, CUDA/PyTorch repos or papers, ML/MLOps careers, GPU mentions in launch or blog posts).
- **FAIL** (hard evidence only) = company shut down or acquired, the person has clearly left or the role is held by someone else, or the work is clearly not GPU-relevant (for example a services shop or pure UI/no-model product). Excluded and never enriched.
- **UNVERIFIED** = nothing conclusive in one search. Not enriched. Goes to a retry queue (second variant search next cycle); after two tries it stays parked. This deliberately replaces the old "doubts never block" rule for the enrich decision only. Doubts still never block a contact whose gate is PASS.
Only PASS contacts go to Step 3. Expect a modest PASS rate, so plan candidate volume as: credits-to-spend / PASS rate. GATE: report PASS / FAIL / UNVERIFIED counts per slice, then proceed to the Step 3 quote for the PASS set only.

## Step 3: credit quote, then reveal
Use Apollo's agent bulk-enrich on the PASS set only, with Jason's instruction: "use only Apollo's own verified emails, no waterfall enrichment, cap at N credits". The agent quotes the cost and pauses. GATE: relay the exact credit total, wait for Jason's explicit yes for that number. Then enrich in chunks of about 500, saving into the Ready Queue list (6b0606b50df6640010b66901) and optionally a "P1 Wave NN" list per chunk. Report credits used after each chunk.

## Step 4: export, rank, queue (transport = Google Sheet)
Jason exports the saved list in the Apollo web app (check the export credit cost shown in the dialog) and imports the CSV into a new tab "Export_Raw" of the Master sheet (File > Import > Insert new sheet). Read it through the Sheets connector, run scripts/prep_queue.py in the sandbox, and write the result to tab `LR_Queue` (same columns as queue.csv) plus an empty `LR_Results` and `LR_State` (lock_heartbeat, paused=FALSE, done=0). Never write contact data to the git repo. Rank: score new contacts with the coarse Notion contact model (page 41c1f31a3ddb8185b833d6f81c67a7f7 and its dimension table), computed like column M of the Master sheet; append to the Master sheet and re-rank everyone.

## Step 5: lean research (Mode C of the skill; Sonnet, medium effort)
Create tabs LR_Queue, LR_Results, LR_State, LR_Usage, LR_Sources, LR_Variants, LR_Playbook, LR_Retro in the Master sheet (headers per the skill). Calibrate first in this interactive session: 20 contacts on Sonnet medium, run validate.py, show Jason 10 rows and the measured tokens per contact (GATE). No model escalation: if quality is poor, fix the playbook and prompt. Then, with Jason's OK, create the scheduled cloud routines lean-research-a/b/c (RemoteTrigger / /schedule): research only, model claude-sonnet-5-5, default environment, repo https://github.com/volofu/apollo-prospects-research, cron in UTC `5 0 * * *`, `10 5 * * *`, `15 10 * * *` (= 7:05pm, 12:10am, 5:15am New York, EST). NO per-run cap: run until the session limit ends the run. The routine prompt must be self-contained: "Read 03_lean_research_skill/SKILL.md and follow Mode C exactly; Google Sheet tabs LR_* hold queue, results, usage and state; run the retro when due; never spend Apollo credits, enrich, enroll or send; never commit contact data."
Token tracking: log one LR_Usage row per batch from each subagent's reported tokens, tool uses and duration; store per-contact estimates in LR_Results; sample exact per-contact tokens every 20th batch. Record anything unmeasurable as `unknown`.
Continuous improvement: run the retro every 200 researched contacts or weekly; update LR_Playbook within the skill's guardrails; once replies exist, join replies back to source type and domain (interactive, weekly).
Weekly 67% pause: cloud runs cannot read usage. Offer Jason a local desktop watchdog task (needs the Claude app open) that reads get_usage every 2 hours, pauses via LR_State and disables the routines at 67%, and re-enables them after the weekly reset (below 20%). Jason chose no per-run cap, so when the computer is off there is no usage check: say this plainly.

## Step 6: write fields and ranks to Apollo
Interactive session. Use apollo_contacts_bulk_create keyed by email with typed_custom_fields (opener, bridge, workload, credit_compute, spend_sentence, Enrichment flags, Notion score, Notion rank) and optional label_names ["P1 Wave NN"]. Test on 3 contacts first: confirm no duplicates, fields updated, and whether label_names appends or replaces. Use batches of 10 to 20 per call and do not echo the responses. If bulk-create is unsuitable, Jason does the CSV import himself (turn "Enrich emails" OFF, test 3 rows).

## Step 7: enroll in rank order
Next about 100 contacts by rank, passed as contact IDs from the sheet; ramp 100, 200, 300, then 350 sends/day (about 33, 67, 100, 117 new contacts per day). Add to the sequence with all 10 mailboxes, Active. Preflight (opt-outs, prior outreach), show Apollo's required enrollment summary once for the whole job, get Jason's explicit confirmation; batches inside the confirmed job need no re-asking. Hold same-company siblings until the lead has received all 3 emails. Log wave, tier and arm in the Master sheet.

## Step 8: monitor weekly
Bounces (auto-pause at 6%), replies, deliverability across the two domains. Slow the ramp if bounces rise. Report reply rate by tier (researched vs scripted) and by template arm.
