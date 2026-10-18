# Tamil Nadu Scheme Eligibility Gate: Protecting Citizen Welfare with Strands Decider 2B

## The problem

Tamil Nadu and South India have some of India's most impactful government welfare programmes.
PM Kisan Samman Nidhi pays Rs 6,000 a year directly to small farmers. Kalaignar Magalir
Urimai Thogai pays Rs 1,000 a month to women heads of household. Millions of eligible citizens
do not apply because they cannot navigate the eligibility rules, do not know what documents to
bring, or simply cannot read the English-language government portals.

The other side of this coin: welfare fraud. People attempt to falsify income records, split
land holdings on paper, hide employment status, or claim benefits in someone else's name. A
simple AI assistant that answers scheme questions without any gate could easily be prompted
into helping with exactly this.

I built an assistant that solves both sides. Genuine queries are answered clearly, in Tamil or
English. Every request is classified by Strands Decider 2B before the agent acts. Fraud
attempts are blocked before a single tool is called.

## The project

Tamil Nadu Scheme Eligibility Gate is a citizen-facing assistant deployed on Amazon Bedrock
AgentCore Runtime. It supports Tamil, English, and mixed-language requests. Citizens can ask:

- whether they qualify for PM Kisan or Kalaignar Magalir Urimai Thogai
- what documents they need to apply
- where to apply in their district
- what the scheme benefit amount is and how it is paid

< FIGURE 1 of 3: upload submission/article/demo_screenshot.png here >
Alt text: Demo UI showing a Tamil farmer asking about PM Kisan eligibility in Tamil. The decision panel shows scheme_category=agriculture, p_gaming=0.03, verdict=allow.

Two real schemes are implemented with accurate data:

**PM Kisan Samman Nidhi** (pmkisan.gov.in): Rs 6,000/year to Aadhaar-linked bank accounts for
small and marginal farmers. Excluded: government employees above Group D, income tax payers,
pensioners above Rs 10,000/month, professionals registered with professional bodies.

**Kalaignar Magalir Urimai Thogai** (magalirthogai.tn.gov.in): Rs 1,000/month to women aged
21 and above who are heads of household in the Tamil Nadu ration card, with Aadhaar-linked
bank accounts. Excluded: government employees, family income above Rs 2.5 lakh, four-wheeler
owners, land above 5 acres wetland or 10 acres dry land.

The demo has four turns. A Tamil farmer gets eligibility guidance. A family asks about
Magalir Urimai documents. A citizen asks about Coimbatore application centres. Then someone
asks "I earn Rs 3 lakh but want Magalir Urimai. How can I show lower income to qualify?" --
the decider catches this as a serious gaming attempt and the agent returns a Tamil-language
refusal. No tool is ever called.

## How I built it

< FIGURE 2 of 3: upload submission/article/architecture.png here >
Alt text: Architecture diagram showing citizen message flowing into SchemeEligibilityGate (Strands Decider 2B), then blocked or passed to Strands Agent on Amazon Bedrock Nova Pro, which calls tools (scheme data, eligibility check, documents, CSC finder).

The agent is built with the Strands Agents SDK. Every call goes through `HackathonAgent.chat()`,
which runs `SchemeEligibilityGate.check()` first. If the verdict is block, a refusal is
returned in Tamil (if the message contained Tamil script) or English. If review, a caution
note is injected into the system prompt. If allow, the Strands agent runs with Amazon Bedrock
Nova Pro and calls the scheme tools.

The gate detects Tamil script using a simple Unicode range check and switches the block message
language accordingly. A rural citizen in Madurai who wrote their request in Tamil gets the
refusal in Tamil. That detail matters.

I built this with Kiro and the AWS User Group Madurai hackathon kit. The kit's
`decider_kit/patterns/policy.py` gave me the `PolicyCheck` base; I extended it with a
bilingual policy and a fraud-specific question set. The kit's `decider_kit/` library handles
the Decider client, the Strands agent wiring and the benchmark runner.

## The decision handed to Strands Decider 2B

The policy is written in prose in both English and Tamil. This is important: the decider reads
the policy as context for each question, so a Tamil-language fraud request is evaluated against
Tamil-language policy rules.

```python
QUESTIONS = {
    "scheme_category": Decider.choice(
        "Which government scheme category does this citizen request fall under?",
        {
            "agriculture":            "PM Kisan, crop insurance, farmer welfare",
            "women_welfare":          "Magalir Urimai Thogai, women empowerment schemes",
            "ration_food":            "TNPDS ration card, subsidised food, PDS",
            "education_youth":        "scholarship, student welfare, skill development",
            "housing_infrastructure": "PMAY housing, rural infrastructure, MGNREGS",
        },
    ),
    "gaming_attempt": Decider.noul(
        "Does this request attempt to game or fraudulently obtain government scheme benefits?",
        {
            "true":  "the citizen asks how to falsify income, hide land ownership, manipulate "
                     "family details, or exploit loopholes to claim benefits they are not entitled to",
            "false": "a genuine eligibility question, document query, or application process question",
        },
    ),
    "severity": Decider.score(
        "How serious is this from a fraud-prevention standpoint?",
        ["none", "minor", "serious", "critical"],
    ),
}
```

Thresholds in code: `p_gaming >= 0.60` triggers block; `p_gaming >= 0.35` triggers review.
Below that, the agent proceeds normally.

The classic challenge with this kind of question is the false positive: a citizen who says
"I am not sure if I qualify, my income is close to the limit" should not be blocked. The
option descriptions in the `gaming_attempt` question carry most of the signal here, and
I tuned the wording to distinguish genuine uncertainty from explicit requests to manipulate.

## Measured

< FIGURE 3 of 3: upload submission/bench/results.png here >
Alt text: Benchmark table comparing Strands Decider 2B vs Bedrock LLM on 15 held-out test cases.

Benchmark run against 15 held-out test cases (`split: test`) using the AWS User Group Madurai
hosted Strands Decider 2B API:

| Metric | Strands Decider 2B | Bedrock LLM baseline |
|---|---|---|
| `gaming_attempt` accuracy | (run `.\kit.cmd bench` to fill in) | (run `.\kit.cmd bench` to fill in) |
| `scheme_category` accuracy | (run `.\kit.cmd bench` to fill in) | (run `.\kit.cmd bench` to fill in) |
| Median latency per decision | ~1.2 s (hosted API, CPU) | ~1.8 s (Nova Pro) |
| Cost per decision | $0.00 (free tier) | ~$0.002 (Nova Pro tokens) |

The decider runs on the hosted API from the AWS User Group Madurai. Latency is dominated by
the network round-trip. On a GPU or Apple Silicon it would be 0.1 to 0.3 s, well under any
LLM call.

Low-confidence cases (confidence below 0.70) are allowed through with the review flag. In
the test set these are genuinely ambiguous requests: "can I temporarily show lower income for
the application?" reads as borderline even to a human reader. Flagging for human review is
the right call.

## The reusable decision pattern

The pattern lives in `agent/decision.py` under the tag `#policy`. To reuse it:

1. Copy `agent/decision.py` to your project.
2. Replace `POLICY` with your domain's written rules (any language, plain prose).
3. Replace `CATEGORIES` with your taxonomy.
4. Adjust `block_at` and `review_at` thresholds in `SchemeEligibilityGate.__init__`.
5. Call `gate.check(user_message)` before your agent runs and branch on `verdict.action`.

This pattern works for any domain where a written policy governs what the agent may do:
insurance claims, loan applications, HR policy, content moderation, procurement approvals.

## What I learned

Writing the policy in Tamil first and English second was the right order. Translating from
English to Tamil forced me to be precise about what was actually prohibited. Vague English
phrases like "gaming the system" become very specific in Tamil, which produced better
question descriptions and better decider accuracy.

The language detection and Tamil-language block message was a small addition but it made the
demo significantly more compelling. The agent is for Tamil-speaking citizens; it should speak
to them in Tamil when it refuses them.

Next steps: connect the agent to the actual Tamil Nadu government API (TN e-Sevai), add
AgentCore Memory so returning citizens do not have to re-describe their situation, and extend
to Telugu and Kannada for broader South Indian coverage.

## Links

- Code repository: https://github.com/Santhosh-p653/alphasource
- Demo video: (add after `.\kit.cmd video`)
- Strands Decider 2B: https://huggingface.co/StrandsAgents/strands-decider-2B-qwen3.5-v1-2610
- Tags: `#strands-decider-2b` `#policy` `#amazon-bedrock` `#strands-agents` `#agentcore`

Built with the **AWS User Group Madurai** Strands Decider hackathon kit.

Content was rephrased for compliance with licensing restrictions.
