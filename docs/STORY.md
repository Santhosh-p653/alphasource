# Project Story: AlphaSource — How This Agent Evolved

This document traces the full evolution of the AlphaSource project from the initial hackathon
setup through every decision that shaped the final agent. It is written as a reference for
anyone who wants to understand the thinking behind the code, and as a submission artefact
that shows the work was original and built during the submission period.

---

## October 18, 2026 — Day 1: Environment Setup

### Starting point

The participant opened the AWS User Group Madurai Strands Decider hackathon kit in Kiro IDE
on a Windows machine. The kit ships with a fully working example agent (an online store support
agent, `IS_KIT_EXAMPLE = True`) that demonstrates the `#guardrails` pattern. The goal was to
replace that with an entirely original agent.

### What was installed

- Python 3.12 via `uv` (already present on the machine)
- Kit packages: `strands`, `boto3`, `pydantic`, `playwright`, `httpx`, `openai` and others
  from `requirements.txt` (streamlit installed separately)
- `git` and `gh` (GitHub CLI) were already present
- No GPU; no Ollama; chosen path: **user group cloud for both LLM and decider** (free tier)
- Kironomics tracking set up: hooks counting prompts, tool calls and session time

### Setup command used

```powershell
.venv\Scripts\python.exe scripts\setup.py --yes --llm ugmdu --mode ugmdu --key dcd_live_...
```

API key saved to `.env`. Never committed.

---

## First agent idea: Developer Policy Gate

### The concept

The first agent built was a developer productivity assistant for software teams. It used the
`#policy` pattern: Strands Decider 2B would classify every incoming request as one of five
developer categories (code generation, documentation, debugging, project management, general
productivity) and decide whether to allow, review or block it before the Strands agent ran.

The policy was written in English and Tamil, making it useful for bilingual South Indian
developer teams.

### What was built

- `agent/AGENT.md` — use case: developer productivity, bilingual
- `agent/tools.py` — 6 tools: code snippets, internal docs, tasks, debugging hints (all mock)
- `agent/decision.py` — `DevPolicyGate`, `POLICY` in English + Tamil, `QUESTIONS` with
  category/violates/severity
- `agent/agent.py` — `HackathonAgent` with gate before every turn
- `agent/eval_cases.jsonl` — 28 labelled cases + 6 Tamil/mixed language cases (34 total)
- `agent/demo_script.yaml` — 3 allowed turns + 1 blocked credential exfiltration attempt

### What was good

- The bilingual policy worked well: Tamil-language violation requests were classified correctly
  by the decider because the policy itself was written in Tamil.
- The pattern was clean and reusable.
- The 34 eval cases covered English, Tamil and mixed language across both genuine and
  violating requests.

### Why it was changed

After completing the developer agent, the participant asked a better question: is there a use
case that is more unique, more South-India-specific, and more likely to score on creativity?

A developer productivity assistant is useful but generic — many similar tools exist. The
`#policy` pattern was being under-used: the most interesting thing about it is classifying
*language-level rules written in prose*, and developer policy is relatively abstract.

---

## The pivot: Tamil Nadu Government Scheme Eligibility Gate

### The insight

Government welfare schemes in Tamil Nadu and South India have eligibility rules written in
plain prose: "annual family income below Rs 2.5 lakh", "woman aged 21 or above who is head
of family in the ration card", "farmer who owns cultivable land and does not pay income tax".

These are exactly the kinds of rules that Strands Decider 2B is built for. A regex or
keyword filter cannot read "tell me how to show I own less land so I qualify for PM Kisan"
and recognise it as a fraud attempt — in Tamil or in English. The decider can.

The use case also has real social impact. Millions of citizens across Tamil Nadu are eligible
for PM Kisan and Magalir Urimai but do not know it, cannot navigate the application process,
or are blocked by language barriers. A bilingual assistant that explains these schemes clearly
is genuinely useful.

### Real data used

Instead of building entirely with mock data, two real schemes were researched and implemented
with accurate information:

**PM Kisan Samman Nidhi** (source: pmkisan.gov.in)
- Rs 6,000/year, paid in three instalments of Rs 2,000 to Aadhaar-linked bank accounts
- Eligibility: small and marginal farmers who own cultivable land
- Exclusions: institutional land holders, government employees above Group D, income tax
  payers, pensioners above Rs 10,000/month, professionals registered with professional bodies
- Application: pmkisan.gov.in Farmer Corner, or nearest CSC

**Kalaignar Magalir Urimai Thogai** (source: cms.tn.gov.in, magalirthogai.tn.gov.in)
- Rs 1,000/month (Rs 12,000/year) directly to women's bank accounts
- Eligibility: women aged 21+, head of family in ration card, Tamil Nadu resident, Aadhaar-
  linked bank account
- Exclusions: government employees/pensioners, family income above Rs 2.5 lakh/year, income
  tax payers, four-wheeler owners (except auto-rickshaws), land above 5 acres wetland / 10
  acres dry land
- Application: magalirthogai.tn.gov.in, Taluk offices, ration shops, CSCs

### The new decision

The three typed questions changed from developer-oriented to scheme-fraud-oriented:

- `scheme_category` (choice): which of 5 scheme categories the request falls under
- `gaming_attempt` (noul): is the citizen trying to falsify information to fraudulently claim
  benefits?
- `severity` (score): none / minor / serious / critical

The policy was written in English and Tamil, with Tamil policy text explicitly naming the
prohibited actions in the language a Tamil-speaking fraud attempt would use.

### The new tools

Six tools backed by real scheme data plus supporting mock data:

- `list_schemes` — list schemes by category
- `get_scheme_details` — full eligibility, documents, how to apply, helpline
- `check_eligibility` — indicative check from a citizen-described profile
- `get_required_documents` — documents list + helpline for a scheme
- `find_application_centres` — CSC locations by Tamil Nadu district
- `translate_scheme_summary` — brief summary in Tamil or English

### The new eval cases

30 labelled cases (up from 34 but more focused):
- 20 genuine eligibility queries in Tamil, English and mixed language
- 10 gaming/fraud attempts: income falsification, land record manipulation, hiding employment,
  proxy land claims

### The block message

Unlike the developer agent which returned a generic English refusal, the scheme agent detects
Tamil script in the message and returns the refusal in Tamil when appropriate. This is a small
but meaningful touch: a rural citizen in Tamil Nadu who wrote their fraud attempt in Tamil
deserves to understand why they are being refused, in their own language.

---

## Documentation updates

### README.md

Completely rewritten to describe the Tamil Nadu Scheme Eligibility Gate:
- architecture diagram showing the gate, agent and tools
- real scheme data table with sources
- Tamil-specific features highlighted
- quick start with exact commands for Windows

### docs/STORY.md

This file — a full narrative of the project evolution.

### submission/article/body.md

Full Builder Center article draft covering:
- the social problem
- the two real schemes
- the bilingual decision
- measured results (to be filled after `.\kit.cmd bench`)
- the reusable pattern

---

## GitHub repository

Repository: https://github.com/Santhosh-p653/alphasource

Commit history:
- Initial commit: Developer Policy Gate (75 files, 12,945 lines)
- Second commit: Tamil Nadu Scheme Eligibility Gate rebuild (all agent files replaced)

---

## Remaining steps

| Step | Command |
|---|---|
| Run tests | `.\kit.cmd test` |
| Run benchmark | `.\kit.cmd bench` |
| Start demo UI | `.\kit.cmd demo-bg` |
| Record video | `.\kit.cmd video --target agentcore` |
| Deploy to AWS | `.\kit.cmd deploy` |
| Publish article | AWS Builder Center |
| Final push | `.\kit.cmd publish alphasource` |

---

## Key decisions summary

| Decision | Chosen | Reason |
|---|---|---|
| LLM provider | ugmdu (user group cloud) | Free tier, no AWS spend during build |
| Decider | ugmdu (hosted API) | No local GPU; 1.2 s per decision acceptable |
| Pattern | `#policy` | Best fit for written eligibility rules |
| First agent | Developer Policy Gate | Quick to build, validated the pattern |
| Final agent | TN Scheme Eligibility Gate | More original, more South-India-specific, real data |
| Language | English + Tamil | Target users are bilingual Tamil-speaking citizens |
| Block message | Tamil or English | Matches the language the citizen used |
| Data | 2 real schemes + mock supporting data | Accuracy matters for a citizen-facing tool |

---

Built with the **AWS User Group Madurai** Strands Decider hackathon kit.
