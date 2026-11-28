# Context, decisions, IDs and state (as of 2026-11-24 evening)

## Goal
Load about 3,500 P1 Startups contacts into the live sequence "P1 Startups - Test (A/B/C)" (id 6aff79b195017e001483701a). 10 mailboxes x 35 sends/day, 3-step sequence (steps at day 0, +3, +6), weekdays for 6 weeks: about 10,500 sends. Ramp 100 -> 200 -> 300 -> 350 sends/day gives about 2,750 contacts; no ramp gives 3,500. Plan for 3,500 as a cushion. Stop starting new contacts about 6 days before the end date so follow-ups finish. Each contact needs an Apollo-sourced VERIFIED email and merge fields opener, bridge, workload (plus credit_compute and spend_sentence because template arm C uses them).

## Decisions by Jason
- 3,500 contacts, 3-step sequence. P1 startups only (no P2, P3, P4).
- No waterfall, ever. Contacts that would need waterfall are skipped for now. Apollo's CSV import UI has "Enrich emails" (waterfall) ON by default: turn it OFF.
- No pilot enrichment needed, but before revealing emails for the whole list: get the credit quote and get Jason's confirmation of the exact number.
- Research for ALL contacts uses Sonnet at medium effort (Jason's choice, replacing the earlier Haiku idea) and the lean, self-improving method in 03_lean_research_skill (source playbook that learns which websites give the best opener/bridge/workload evidence; token usage tracked per batch in the Master sheet tabs LR_*). Intent: run off-peak (7pm-9am) and until the session limit, pause when weekly usage reaches 67%. Environment chosen 2026-11-24: Claude Code cloud (interactive cloud session for credit and enrollment steps, scheduled cloud routines for research only; see skill Mode C). Cloud routines cannot read usage, so the 67% cap needs a local desktop watchdog (works only while the Claude app is open). Jason chose NO per-run contact cap. Repo: https://github.com/volofu/apollo-prospects-research (docs and scripts only; contact data lives in Google Sheets).
- 2026-11-25: pre-enrichment gate. No email reveal until the contact is researched online and PASSES: company live, person still in role, GPU-compute reliance evidenced (runbook Step 2b, skill R0). Candidates are cleaned in the cloud session first (3,332 company-screened candidates exist in a local file final_candidates.tsv, git-ignored; contact research for them has NOT been run yet).
- Doubts become DUBIOUS notes (Apollo field "Enrichment flags", Master sheet columns CU:CX). Never block on doubts, except that UNCONFIRMED contacts are not enriched until the gate passes.
- One lead per company first. Same-company co-founders are held until the lead has received all 3 emails (add them later).
- Rank, score, wave and tier are recorded in the Master sheet and may also be written to Apollo: existing contact fields "Notion score (post-enrichment)" and "Notion rank (post-enrichment)", plus optional "P1 Wave NN" Apollo lists. Enroll in rank order using contact IDs from the sheet; Apollo lists are a convenience, not the mechanism.
- The earlier Apollo "score sync" CSV import is dropped as a separate step; score and rank can ride along in the same write as the merge fields.

## IDs
- Master sheet: 1CsfEUmnch_cbk6l8NCQbWqK0Cn1nCqeoF_019DdwsUg. Tab "Master Scoring & Research Sheet": contact id col A, Notion score col M, Notion rank col P, Company P1 rank col Z, DUBIOUS columns CU:CX. Other tabs: "Apollo score sync" (id, score, rank for 1,485 contacts), "Pilot 20 companies", "Sample CSV for Apollo".
- Apollo lists: "P1 Startups – People" 6afd347df760960014056b3a (1,485 contacts), "P1 Startups – Companies" 6afd347c7f5c790018d06445 (2,630 accounts with P1 Rank / Overall Score custom fields), Ready Queue "P1 Startups - Ready Queue (verified email, not yet sequenced)" 6b0606b50df6640010b66901. Other persona lists exist (P2 6afd347ef760960014056b41, P3 6afd347e5e55a50018ff6d1c, P4 6afd347e475bf00018d8f547): do NOT use.
- Contact custom field ids: opener 6aff78e9f68e23000cc79c03; bridge 6aff79119d6d8300188f886d; workload 6aff793f9d6d8300188f8a2a; credit_compute 6aff7949dc19c0000cc03bfb; spend_sentence 6aff7928241c35000c2d69e9; funding_stage 6aff795411dac900105f5ae7; est_monthly_gpu_spend 6aff796a1b97a300181ceddf; est_monthly_savings 6aff79751b97a300181cee36; credit_variant 6aff798337e1000020b63faa; Enrichment flags 6afe23d855b161002094b0e1; Enrichment evidence 6afe23bfa270a3000c26dd92; Notion score 6afe23411fc7730020b31195; Notion rank 6afe2370b1b05f0010e26932; Apollo score 6afe23ab29ccb7001879817c.
- Sending mailboxes (rotate all 10): 6ae4e9f386cc3300100f07bb, 6ae522f6f545fb001c0793b9, 6ae5268308544b0014ca8dba, 6ae522724f68d6001c5c2247, 6ae526ca0a2802000ca73304, 6ae524fdf2ee14001c599b8e, 6ae521b11f18850010c77459, 6ae51ce4b85cc7001857382d, 6ae527930b2dc90010acfadf, 6ae4ebe30d36e60020609799. They sit on only two domains (aghneocloud.com and udutechnologies.com), 175 sends/day per domain at full rate.
- Notion scoring model (CURRENT 2026-11-18): contact model page 41c1f31a3ddb8185b833d6f81c67a7f7, company model page 41c1f31a3ddb818188fcc26b68190ff3; contact dimension table collection d531f31a-3ddb-82a9-aca1-8736e38d22b5.

## Current state
- 10 trial contacts (Boris Iskrev, Alexandros Petkos, Frank Teoh, Jonathan Lightner, Daniel Benjamin, Vitalay Fomin, Thore Buergel, Mehul Agarwal, Axel Peytavin, Antonio Monreal) were re-enrolled Active at step 1 on 2026-11-24 with hand-written merge fields. Earlier they had failed with "snippets_missing" because the merge fields were empty.
- About 85 earlier contacts are mid-sequence (13 of the 20 top-ranked pilot companies were already emailed).
- Waterfall-enriched, merge fields written, in the Ready Queue list, NOT yet sequenced: Ivan Avanesov (Splash), Lukas Martinelli (Reprompt), Tony Zhang (Tera AI), Rajini Anachi (AVAWATZ), Dima Kislovskiy (Swan), Kia Khezeli (YRIKKA). Held out pending Jason: Jack Norris (RapidFire; one validator says his email is invalid, not written to his record) and Pi Zonooz (one validator says do-not-mail; Apollo says verified).
- Held siblings (a co-founder is already in the sequence): Sai Vemprala 6afd39a24f693b001865522c, Eli Mann 6afd39a44a0cf7000c5d0178, Brad Chisum 6afd39a477ebe600218db22f, Shadi Elaridi 6afd39a634563e00104d4357, Sebastian Peralta 6afd39a509eb740010256112, Alex Senemar 6afd39a26113c9001471838f, TJ Ragsdale 6afd39a2b3b22100183be300, Alex Neff 6afd39a7bb5e280018e6c655, John Kalantari 6afd39a57655030018d471f1, Akhror B (Unitlab CTO, not enriched).
- Credits: about 47,100 left. Spent so far about 20 (2 on company pages, 18 on a waterfall enrichment of 7 people, which is why waterfall is banned).
- Weekly Claude usage was 64% on 2026-11-24 evening and resets about 7:59pm local on 2026-11-25.

## Free facts
- Apollo people search (US, 1-50 employees, AI/ML keywords, founder or C-suite) = 25,394 people; filter contact_email_status ["verified"] = 21,272 (84%). One slice, not a promise: re-measure on the real candidate set.
- Of the top 20 ranked companies, most already have contacts and many of those are already emailed, so most net-new contacts must come from new companies.

## Lessons learned
- apollo_contacts_update and bulk calls return about 4K tokens per contact. In a normal chat use small batches (10 to 20) or let Jason do the CSV import himself.
- apollo_contacts_bulk_create (max 100 per call) dedupes by email, updates existing contacts, and can set typed_custom_fields and label_names in the same call. Test on 3 contacts first, including whether label_names appends or replaces existing lists.
- Apollo's agent bulk-enrich picks waterfall by default when the team has it: always instruct "Apollo's own verified emails only, no waterfall".
- Apollo HQ and title data is often wrong; verify before flagging location.
- Template arm C needs credit_compute and spend_sentence or step 1 fails with snippets_missing. Follow-up steps use {{contact.workload}}.
