# Apollo notes (from the Nov 2026 "Apollo for Agents" webinar, deck and magazine article, plus our own testing)

## What Apollo says (paraphrased)
- Apollo's agent can be driven from Claude/ChatGPT. Seeing leads is free on any plan; saving contacts or adding them to sequences needs a Professional or Organization plan (Jason has it).
- Magazine prompt 1: find decision makers matching the saved ICP, one per company, not already in the account, verified email, "Apollo-only verification, under 20 credits"; agents show a credit estimate and wait for approval. We adopt the credit-cap and Apollo-only wording, never waterfall.
- "1:1 email sequences" push a unique email per contact in one step, no custom fields (add-contacts-to-sequence has step_content_overrides). We use merge fields for the bulk and overrides only for special cases, because writing emails per contact through a chat does not scale.
- Apollo's AI scoring "research fields", Google Maps / AI research and waterfall all spend credits. Our own Notion scores make the scoring prompt unnecessary.
- The deck lists phone/email verification "including your own lists". Cost unknown; test on 1 contact before relying on it.
- Context Center (Apollo settings) feeds the agent. Not needed for our flow.
- Nothing in the webinar saves credits; treat suggestions to use Apollo AI features as spending decisions.

## Our testing facts
- Standard people search is free; company search costs 1 credit per page of 100; standard enrichment is 1 credit per match; a waterfall enrichment of 7 people cost 18 credits.
- Apollo CSV import UI: "Enrich emails" (waterfall) defaults ON and would have cost 1,485 to 5,940 credits for our file. Always switch it OFF. A contact CSV needs at least one identifier (email, company name, website, or LinkedIn URL) for matching.
- Contact updates and bulk calls return large payloads (about 4K tokens per contact).
- email_status "verified" in Apollo can still disagree with third-party validators (example: one validator marked a "verified" address invalid, another do-not-mail). Expect 1 to 3% bounces; the sequence auto-pauses at 6%.
- Webinar captions are saved in Downloads as apollo-webinar-prompt-agents-captions-en.txt if ever needed (not part of this project folder to keep context small).
