# Live sequence "P1 Startups - Test (A/B/C)" (id 6aff79b195017e001483701a)
Schedule "Normal Business Hours" (America/Los_Angeles). 3 auto-email steps: step 1 at day 0 (three step-1 variants A/B/C), step 2 after 3 days, step 3 after 3 more days. Open tracking is off. Reply, interested and out-of-office stop the sequence. Auto-pause at 6% bounces (7-day window, min volume 200).

## Step 1 (subject for all arms: "$333 in GPU credit for $33")
Shared opening: "Hi {{first_name}}, Get $333 in GPU cloud credit for as little as $33. Plus, up to $583 in additional discounts and rates reliably 30-40% below the big hyperscalers' going forward. Pretty sweet, right?" then "{{contact.opener}} {{contact.bridge}}"
- Arm A: "The credit alone is real runway for {{contact.workload}}. I'm Jason at AGH Cloud, an emerging US GPU neocloud with a brand new program for early-stage AI startups."
- Arm B: "I'm Jason, a Cornell MBA with a VC background, now running US startup sales at AGH Cloud, an emerging US GPU neocloud with a brand new program for early-stage AI startups. Teams running {{contact.workload}} are exactly who it's for."
- Arm C: "I'm Jason at AGH Cloud, an emerging US GPU neocloud, and this is our brand new AGH Cloud for Startups program. That $333 covers {{contact.credit_compute}} for {{contact.workload}}. {{contact.spend_sentence}}"
Shared close: Reply "Yes" or "interested" and I'll send the program details. Only 30 spots, and they're going fast. Would be great to welcome you to the first cohort. Not for you? Reply "no" and I won't follow up.

## Step 2 (3 variants, replies in thread)
1. "Hi {{first_name}}, Quick bump: $333 in GPU credit for as little as $33, which goes a long way for {{contact.workload}}, and the first cohort is filling. Reply "Yes" and I'll send the details. Not for you? Reply "no" and I won't follow up."
2. "The $333-for-$33 credit is still open. Same program: GPUs 30-40% below hyperscaler on-demand, no long contracts, 30 spots in the first cohort. Reply "Yes" or "interested" for the details. Not for you? Reply "no" and I won't follow up."
3. "Following up on the $333-for-$33 GPU credit for {{contact.workload}}. Happy to send the program details: just reply "Yes" or "interested." The first cohort is capped at 30. Not for you? Reply "no" and I won't follow up."

## Step 3 (3 variants, replies in thread)
1. "Last note from me. If GPU spend isn't a problem yet, no worries. If it will be, reply "interested" and I'll send the details while there are still spots in the first cohort. Not for you? Reply "no" and I won't follow up."
2. "Last note from me. If GPU costs are on your horizon, reply "interested" and I'll send the details while the first cohort still has room. Not for you? Reply "no" and I won't follow up."
3. "Last note from me. If cheaper GPUs with no long contract would help, reply "interested" and I'll send the program details while the first cohort still has spots. Not for you? Reply "no" and I won't follow up."

## Required merge fields per contact
first_name, contact.opener, contact.bridge, contact.workload, and (arm C only) contact.credit_compute, contact.spend_sentence. A missing field fails step 1 with "snippets_missing".
Fallback values: credit_compute heavy "about 22 hours on an 8x A100 80GB node", light "about 40 hours on a 4x L40 node". spend_sentence (stage unknown): "For reference, a typical seed-stage startup running GPUs on a hyperscaler pays around $8-20K a month, and even our list rates, without the startup discounts, would save $2.5-8K of that. By Series B the same bill is often $50-200K a month, so the savings grow to $15-60K, which is why switching early is easier than switching later."
