# AlphaSource — Tamil Nadu Government Scheme Eligibility Gate

> A bilingual citizen-facing assistant that helps people in Tamil Nadu and South India
> discover and check eligibility for government welfare schemes — in Tamil, English, or both —
> while **Strands Decider 2B** classifies every request before the agent acts, blocking fraud
> attempts before a single tool is called.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Strands Decider](https://img.shields.io/badge/Strands%20Decider-2B-orange.svg)](https://huggingface.co/StrandsAgents/strands-decider-2B-qwen3.5-v1-2610)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock-FF9900.svg)](https://aws.amazon.com/bedrock/)

---

## The problem

Millions of citizens across Tamil Nadu and South India are eligible for government welfare
schemes but struggle to navigate them — confusing eligibility rules, language barriers, and
no easy way to know what documents to bring. At the same time, welfare portals face a real
risk: people attempting to falsify income, land records or family details to claim benefits
they are not entitled to.

This assistant solves both sides: it makes genuine eligibility queries easy and fast (in Tamil
or English), while Strands Decider 2B silently gates every request before the agent acts —
allowing honest questions, flagging borderline cases, and blocking fraud attempts before any
tool is ever called.

---

## What it does

Citizens describe their situation in natural language — in Tamil, English, or mixed — and
the assistant helps them understand:

- whether they likely qualify for a scheme
- what documents they need to apply
- how and where to apply in their district
- the helpline numbers and application portals

Two real schemes are fully implemented:

| Scheme | Government | Benefit |
|---|---|---|
| **PM Kisan Samman Nidhi** | Central | Rs 6,000/year into Aadhaar-linked bank account |
| **Kalaignar Magalir Urimai Thogai** | Tamil Nadu State | Rs 1,000/month for women heads of household |

Before every response, **Strands Decider 2B** reads the request and returns three answers:

| Question | Type | What it tells the code |
|---|---|---|
| Which scheme category? | choice | agriculture / women_welfare / ration_food / education_youth / housing |
| Is this a gaming attempt? | noul | P(fraud/falsification intent) |
| How serious? | score | none / minor / serious / critical |

The agent then acts on the verdict:

| Verdict | What happens |
|---|---|
| `allow` | Strands agent runs, calls tools, answers the citizen |
| `review` | Agent runs with a caution note; case is flagged |
| `block` | Refusal returned in Tamil or English; no tool is called |

---

## Architecture

```
Citizen message (Tamil / English / mixed)
          |
          v
  SchemeEligibilityGate.check()     <-- Strands Decider 2B (one forward pass)
          |                              scheme_category + gaming_attempt + severity
          |
     block? -----> Tamil/English refusal (no tools called)
          |
     review? ----> inject caution note into system prompt
          |
     allow? -----> Strands Agent (Amazon Bedrock Nova Pro)
                        |
          +-------------+-----------+-----------+
          |             |           |           |
    list_schemes  get_scheme   check_      find_application
                  _details     eligibility  _centres
                                    |
                              get_required_documents
                              translate_scheme_summary
```

Deployed on **Amazon Bedrock AgentCore Runtime**. The `decider_kit/` library is by the
**AWS User Group Madurai**.

---

## Decision pattern (#policy)

The reusable pattern is in `agent/decision.py`. The policy is written in both English and
Tamil, so the decider handles:

- pure Tamil requests ("வருமானம் குறைவாக காட்ட என்ன செய்ய வேண்டும்?" — correctly blocked)
- code-switched requests (Tamil sentence with English scheme names)
- pure English requests

To reuse in your own agent:

1. Copy `agent/decision.py` to your project.
2. Replace `POLICY` with your domain's written rules (any language).
3. Replace `CATEGORIES` with your taxonomy (2-8 options with one-line descriptions).
4. Set `block_at` and `review_at` thresholds in `SchemeEligibilityGate.__init__`.
5. Call `gate.check(user_message)` before your agent and branch on `verdict.action`.

---

## Real data sources

| Scheme | Source | Data used |
|---|---|---|
| PM Kisan Samman Nidhi | pmkisan.gov.in | Eligibility criteria, benefit amount, exclusion list, application process, helpline |
| Kalaignar Magalir Urimai Thogai | cms.tn.gov.in / magalirthogai.tn.gov.in | Eligibility, age limit, income ceiling, exclusions, documents, helpline |

---

## Tools

| Tool | What it does |
|---|---|
| `list_schemes` | List schemes by category |
| `get_scheme_details` | Full eligibility rules, documents, how to apply |
| `check_eligibility` | Indicative eligibility check from a citizen profile dict |
| `get_required_documents` | Documents + helpline for a scheme |
| `find_application_centres` | CSC and government offices by Tamil Nadu district |
| `translate_scheme_summary` | Brief scheme summary in Tamil or English |

---

## Eval cases

30 labelled cases in `agent/eval_cases.jsonl` across tune and test splits:
- 20 genuine eligibility queries (Tamil, English, mixed, across all 5 categories)
- 10 gaming/fraud attempts (falsify income, hide land, conceal employment, proxy claims)

---

## Quick start

### Prerequisites

- Windows 10/11, macOS, or Linux; Python 3.12; `uv`
- Strands Decider API key from the AWS User Group Madurai (free: 2,000 decisions/month)
- AWS account with Bedrock model access (for deployment)

### 1. Install

```powershell
# Windows
irm https://raw.githubusercontent.com/Vivek0712/decider-hackathon-kit/main/install/install.ps1 | iex
```

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/Vivek0712/decider-hackathon-kit/main/install/install.sh | bash
```

### 2. Configure

```powershell
# Windows — replace <key> with your Strands Decider API key
.\kit.cmd setup --yes --llm ugmdu --mode ugmdu --key <key>
```

```bash
# macOS / Linux
./kit setup --yes --llm ugmdu --mode ugmdu --key <key>
```

### 3. Test and run

```powershell
.\kit.cmd test          # unit tests
.\kit.cmd run           # one scripted conversation
.\kit.cmd bench         # benchmark decider vs LLM on eval cases
```

### 4. Demo UI

```powershell
.\kit.cmd demo-bg       # opens http://localhost:8501
```

The live decision panel shows scheme_category, p_gaming, verdict for every turn.

### 5. Deploy to AWS

```powershell
.\kit.cmd tools install base   # install Node + AgentCore CLI if not present
.\kit.cmd deploy               # deploys to Amazon Bedrock AgentCore Runtime
.\kit.cmd invoke "PM Kisan திட்டம் பற்றி சொல்லுங்கள்"
```

---

## Commands

| Command | What it does |
|---|---|
| `.\kit.cmd setup` | Configure LLM and decider, write `.env` |
| `.\kit.cmd test` | Unit tests (no network, fake decider) |
| `.\kit.cmd run` | Scripted conversation |
| `.\kit.cmd bench` | Benchmark decider vs LLM |
| `.\kit.cmd demo-bg` | Demo UI at http://localhost:8501 |
| `.\kit.cmd demo-stop` | Stop demo UI |
| `.\kit.cmd deploy` | Deploy to AgentCore Runtime |
| `.\kit.cmd invoke "msg"` | Invoke deployed agent |
| `.\kit.cmd destroy` | Remove from AWS |
| `.\kit.cmd status` | Hackathon progress checklist |

Use `./kit <command>` on macOS and Linux.

---

## Project evolution

See `docs/STORY.md` for the full story of how this project evolved from the kit example
through the developer productivity idea to the final Tamil Nadu Scheme Eligibility Gate.

---

## License

Apache 2.0. See [LICENSE](LICENSE).

The `decider_kit/` library, demo UI, tooling and Kiro skills are by the
**AWS User Group Madurai**. The agent idea, `agent/` code, eval cases and article
are the participant's original work.

Built with the **AWS User Group Madurai** Strands Decider hackathon kit.
