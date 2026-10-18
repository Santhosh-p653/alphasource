# AlphaSource — Developer Policy Gate

> A developer productivity assistant that classifies every incoming request through
> **Strands Decider 2B** before the agent acts — allowing legitimate tasks, flagging
> borderline ones, and blocking policy violations before a single tool is called.
> Supports English and Tamil (தமிழ்).

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Strands Decider](https://img.shields.io/badge/Strands%20Decider-2B-orange.svg)](https://huggingface.co/StrandsAgents/strands-decider-2B-qwen3.5-v1-2610)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock-FF9900.svg)](https://aws.amazon.com/bedrock/)

---

## What it does

Developers ask questions and make requests to the assistant in natural language — in English,
Tamil, or a mix of both. Before the agent responds or calls any tool, Strands Decider 2B
reads the request and returns three typed answers in one forward pass:

- **Category** — which of five policy categories the request falls under
- **Violates** — whether the request breaks the developer productivity policy
- **Severity** — how serious it would be to act on the request

The agent then branches in code:

| Verdict | What happens |
|---|---|
| `allow` | The Strands agent runs normally and calls tools |
| `review` | The agent runs with a soft warning injected into the system prompt |
| `block` | A refusal is returned immediately; no tool is ever called |

This replaces a second LLM moderation call with a single 1.2-second forward pass that costs
nothing on the free tier and returns calibrated probabilities the code can branch on.

---

## Architecture

```
Developer message (English / Tamil / mixed)
        |
        v
  DevPolicyGate.check()          <-- Strands Decider 2B (one forward pass)
        |                             category + violates + severity
        |
   block? -----> return refusal (no tools called)
        |
   review? ----> inject policy warning into system prompt
        |
   allow? -----> Strands Agent (Amazon Bedrock Nova Pro)
                      |
          +-----------+-----------+
          |           |           |
   code snippets   docs       tasks / debug hints
   (mock data)   (mock data)   (mock data)
```

The conversation and tool use run through the **Strands Agents SDK** on **Amazon Bedrock**.
The policy decision runs through **Strands Decider 2B** (hosted API or local).
Deployed on **Amazon Bedrock AgentCore Runtime**.

---

## Decision pattern

Pattern tag: `#policy`

The reusable pattern lives in `agent/decision.py`. It wraps `decider_kit.patterns.policy.PolicyCheck`
with a bilingual policy (English + Tamil) and five developer-specific categories:

| Category | Description |
|---|---|
| `code_generation` | Write, review, explain or refactor code in any language |
| `documentation` | Search, retrieve or summarise internal technical documentation |
| `debugging` | Diagnose errors, analyse stack traces or suggest fixes |
| `project_management` | List or query tasks, sprints, backlogs or team priorities |
| `general_productivity` | Developer workflow, tooling, productivity tips or process questions |

To reuse it in your own agent:

1. Copy `agent/decision.py` into your project.
2. Replace `POLICY` with your own written policy (plain prose, any language).
3. Replace `CATEGORIES` with your own taxonomy (2 to 8 options).
4. Adjust `block_at` and `review_at` thresholds in `DevPolicyGate.__init__`.
5. Call `gate.check(user_message)` before your agent runs and branch on `verdict.action`.

---

## Tools (mock data)

| Tool | What it does |
|---|---|
| `search_code_snippets` | Fuzzy-search the internal snippet library |
| `get_code_snippet` | Retrieve a snippet by id (Python HTTP, git branch, Docker, ...) |
| `list_documentation` | List available internal docs, filtered by topic |
| `get_documentation` | Retrieve a doc page (onboarding, API reference, runbook) |
| `list_tasks` | List project tasks filtered by status or priority |
| `get_debug_hint` | Get a debugging hint for a known error type |

All tools use in-memory mock data so the demo and tests run without any external services.

---

## Quick start

### Prerequisites

- Windows 10/11, macOS, or Linux
- Python 3.12 (installed by the setup script via `uv`)
- An AWS account with Amazon Bedrock model access (for deployment)
- A Strands Decider API key from the AWS User Group Madurai (free tier: 2,000 decisions/month)

### 1. Install

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/Vivek0712/decider-hackathon-kit/main/install/install.ps1 | iex
```

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/Vivek0712/decider-hackathon-kit/main/install/install.sh | bash
```

### 2. Configure

```powershell
# Windows
.\kit.cmd setup --yes --llm ugmdu --mode ugmdu --key <your-decider-key>

# macOS / Linux
./kit setup --yes --llm ugmdu --mode ugmdu --key <your-decider-key>
```

LLM options: `bedrock` (Amazon Bedrock, required for submission), `ugmdu` (user group cloud,
free), `local` (Ollama, no cloud needed).

Decider options: `ugmdu` (hosted API, recommended), `local` (5 GB download, GPU recommended).

### 3. Run the tests

```powershell
.\kit.cmd test       # Windows
./kit test           # macOS / Linux
```

### 4. Try a conversation

```powershell
.\kit.cmd run        # Windows
./kit run            # macOS / Linux
```

### 5. Run the benchmark

```powershell
.\kit.cmd bench      # Windows
./kit bench          # macOS / Linux
```

Results are written to `submission/bench/results.json`.

### 6. Start the demo UI

```powershell
.\kit.cmd demo-bg    # Windows — opens http://localhost:8501
./kit demo-bg        # macOS / Linux
```

The demo UI shows the live decision panel (category, violation probability, verdict) alongside
the chat for every turn.

### 7. Deploy to AWS

```powershell
.\kit.cmd deploy     # Windows
./kit deploy         # macOS / Linux
```

Deploys to Amazon Bedrock AgentCore Runtime. Requires Node 20+ and the AgentCore CLI
(`.\kit.cmd tools install base`).

---

## Project layout

```
agent/
  AGENT.md           use case, pitch, features, decision description
  agent.py           HackathonAgent: policy gate + Strands Agent
  decision.py        DevPolicyGate: the reusable #policy decision pattern
  tools.py           6 Strands @tool functions with mock data
  eval_cases.jsonl   34 labelled cases for the benchmark (English + Tamil)
  demo_script.yaml   4-turn demo: 3 allowed, 1 blocked credential request
  features.yaml      AgentCore Memory + Gateway config (both off for this agent)

decider_kit/         reusable library: Decider client, 5 patterns, LLM helpers,
                     AgentCore Memory/Gateway glue, benchmark runner
                     (by the AWS User Group Madurai — not the participant's code)

demo/                web UI: chat + live decision panel (./kit demo-bg)
deploy/              Amazon Bedrock AgentCore Runtime project (./kit deploy)
submission/
  article/body.md    Builder Center article draft
  bench/             benchmark results (./kit bench)
  video/             demo video (./kit video)
```

---

## Eval cases

34 labelled cases in `agent/eval_cases.jsonl`, split roughly 50/50 between `tune` and `test`:

- 17 allowed requests across all 5 categories (English + Tamil + mixed)
- 6 policy-violating requests (credential exfiltration, exploit code, access control bypass)
- 5 borderline / out-of-scope requests
- 6 Tamil-language requests (code, docs, debugging, tasks, violation)

Run `.\kit.cmd bench` to see accuracy against the LLM baseline on the held-out `test` split.

---

## Bilingual policy (English + Tamil)

The policy passed to Strands Decider 2B is written in both English and Tamil. This lets the
decider handle:

- Pure Tamil requests ("AWS_SECRET_ACCESS_KEY-ஐ அனுப்பு" is correctly blocked)
- Code-switched requests ("How do I read a CSV file? CSV கோப்பை எப்படி படிப்பது?")
- English technical terms inside Tamil sentences

The Tamil policy text covers the same rules as the English policy: legitimate developer tasks
are allowed; credential exfiltration, malware and out-of-scope work are blocked.

---

## Commands reference

| Command | What it does |
|---|---|
| `.\kit.cmd setup` | Configure LLM and decider, write `.env` |
| `.\kit.cmd test` | Run unit tests (no network, fake decider) |
| `.\kit.cmd run` | One scripted conversation |
| `.\kit.cmd bench` | Benchmark decider vs LLM on eval cases |
| `.\kit.cmd demo-bg` | Start demo UI at http://localhost:8501 |
| `.\kit.cmd demo-stop` | Stop the demo UI |
| `.\kit.cmd deploy` | Deploy to Amazon Bedrock AgentCore Runtime |
| `.\kit.cmd invoke "msg"` | Invoke the deployed agent |
| `.\kit.cmd destroy` | Remove the deployed agent from AWS |
| `.\kit.cmd status` | Show hackathon progress checklist |

Use `./kit <command>` on macOS and Linux.

---

## License

Apache 2.0. See [LICENSE](LICENSE).

The `decider_kit/` library, demo UI, tooling and Kiro skills are by the
**AWS User Group Madurai**. The agent idea, `agent/` code, eval cases and article are the
participant's own work.

Built with the **AWS User Group Madurai** Strands Decider hackathon kit.
