# Prompt for a new chat: reliable, compliant web search at scale for contact confirmation

Paste everything below the line into a new Claude chat with web search enabled. It contains no contact data.

---

I run outbound sales for a US GPU cloud ("neocloud") startup program. Before spending an email-reveal credit, I confirm that a startup contact is still in their role by running web searches, including LinkedIn "X-ray" queries such as `site:linkedin.com/in "First" "Company" founder`, and reading only the titles and snippets on the search results page. I never open linkedin.com, log in, or use fake accounts.

PROBLEM
The search tool I have today (a built-in agent web search) returns only titles and URLs, with no snippet text, and approximates the `site:` operator. Real Google would be better (snippets, exact phrases, `site:`), but automated Google searching hits rate limits and CAPTCHAs quickly. I need a reliable, compliant way to run searches at scale.

SCALE
About 3,300 contacts now; later tens to hundreds of thousands. Assume 1 to 4 searches per contact, so roughly 3,000 to 13,000 queries now and up to 100k to 1M+ queries later. Queries come from a script (company name, first name, role keyword, optional boosters such as H100, Llama, vLLM, fine-tuning, AWS, on-prem). Results are parsed by code, then judged by a model.

WHAT I WANT YOU TO RESEARCH
1. Licensed search APIs and SERP data providers that return organic results with snippets. Compare at least: Google Programmable Search / Custom Search JSON API, Brave Search API, Bing alternatives (check the current status of Microsoft's Bing Search APIs), Serper, SerpAPI, Tavily, Exa, Kagi, You.com, Perplexity search API, DuckDuckGo-based options. For each: price per 1,000 queries at my volumes, free tier, rate limits, whether `site:` and exact-phrase operators work, snippet length and freshness, whether LinkedIn results appear with usable titles/snippets, terms of service, and reliability reports.
2. Whether any provider's terms or LinkedIn's terms create legal or account risk for reading LinkedIn results through search snippets. State uncertainty plainly and cite sources.
3. Operating options for running real Google through a browser (for example from a local machine, human-paced): realistic safe daily volume, what triggers blocks, and what is permitted. Assess proxy and VPN rotation purely as a risk question: what the terms say, what the risk is to my IPs, domains and accounts. Do not design or recommend CAPTCHA solving, CAPTCHA-bypass services, fake accounts, or techniques whose purpose is to evade a site's access controls. If a compliant path is not available, say so.
4. Non-search ways to get the same facts: company and team pages, GitHub orgs, YC/Wellfound/Crunchbase/Product Hunt, press releases, podcasts, conference speaker pages, patent and paper author lists, SEC/Form D filings, and any licensed B2B datasets (price, coverage of 1-50 person US startups, freshness of job titles).
5. Compatibility with my setup: my agents run in Claude Code cloud sessions with a network allowlist (hosts must be added to the environment), API keys are saved through a secure credential form (never pasted in chat), each subagent run has a cap of roughly 60 web searches, and the built-in WebFetch is blocked in workers.

OUTPUT
- A comparison table (provider, cost per 1k queries at 10k / 100k / 1M, snippet quality, `site:` support, LinkedIn coverage, terms risk, setup effort).
- A recommended stack for (a) the next 3,300 contacts and (b) 100k+ contacts, with a monthly cost estimate and the main risks.
- A 30-contact test plan: use the same first name + company + role queries, measure (i) share of contacts whose current role is confirmed, (ii) share where the full last name is found, (iii) cost per confirmed contact. My baseline from the built-in search is 70% role confirmed and 87% last name found on 30 contacts at roughly 15,000 model tokens per contact.
- Clear flags for anything you could not verify. Prefer primary sources (provider pricing and terms pages) over blog posts.
