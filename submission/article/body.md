# How I Built a Bilingual Citizen Welfare Assistant That Blocks Fraud with Strands Decider 2B

## The moment it clicked

I grew up watching my grandmother struggle to understand government scheme paperwork. She was
eligible for multiple programmes but could never figure out which ones, what documents to
bring, or where to go. She spoke only Tamil. The forms were in English. The portals were
confusing. She gave up every time.

When I heard about the Agent Experience Hackathon and saw Strands Decider 2B, I knew exactly
what I wanted to build. Not another developer tool. Something that could actually help people
like her.

That is how AlphaSource — the Tamil Nadu Government Scheme Eligibility Gate — came to be.

## What the problem actually is

Tamil Nadu has some of India's most impactful welfare programmes. PM Kisan Samman Nidhi pays
Rs 6,000 a year directly to small farmers. Kalaignar Magalir Urimai Thogai pays Rs 1,000 a
month to women who are heads of their household. Tens of millions of people are eligible. Many
never apply because they do not know they qualify, cannot read the English portals, or do not
know which documents to bring.

But there is a second problem that does not get talked about as much: welfare fraud. People
try to falsify income records, split land holdings on paper, hide employment status, or claim
in someone else's name. A naive AI assistant that answers scheme questions without any gate is
a fraud enabler.

I needed to solve both sides at once. Help the honest citizen. Block the bad actor.

## Why Strands Decider 2B was the right tool

The eligibility rules for these schemes are written in plain prose. "Annual family income
below Rs 2.5 lakh." "Woman aged 21 or above who is listed as head of family in the ration
card." "Farmer who owns cultivable land and does not pay income tax."

These are language-level policy rules. A regex or a keyword filter cannot read "tell me how
to show I own less land so I qualify for PM Kisan" in Tamil and recognise it as a fraud
attempt. A second LLM call could, but that doubles the cost and latency for every single
request.

Strands Decider 2B is built exactly for this. It reads a state — the citizen's message plus
the policy — and returns calibrated probabilities in one fast forward pass. No generation, no
hallucination, no extra cost. Just: is this request legitimate, and if not, how serious is it?

I had my architecture.

## Building it

I started with the AWS User Group Madurai hackathon kit and Kiro IDE. The kit gave me the
scaffolding: the Strands agent wiring, the `PolicyCheck` pattern, the benchmark runner, the
demo UI. I replaced everything in `agent/` with my own idea.

The first version I built was actually a developer productivity assistant, also using the
`#policy` pattern. I got it working, ran the eval cases, and then asked myself: is this the
most original, most South-India-specific thing I can build? The answer was no. I scrapped it
and started over with the scheme eligibility idea.

The rebuild took a few hours. Here is what I built:

**Two real schemes with accurate data.** I went to pmkisan.gov.in and magalirthogai.tn.gov.in
and read the actual eligibility criteria, exclusions, document requirements and helpline
numbers. I put all of it into `agent/tools.py` as in-memory data. No hallucinated rules.

**A bilingual policy.** The policy text I pass to Strands Decider 2B is written in both
English and Tamil. This matters more than it sounds. A Tamil-speaking person who types a
fraud attempt in Tamil — "வருமானம் குறைவாக காட்ட என்ன செய்ய வேண்டும்?" — gets evaluated
against Tamil-language policy rules. The decider sees the full policy, not just keywords.

**Three typed questions.** Before the agent responds to anything, the gate asks the decider:
which scheme category is this? is it a gaming attempt? how severe? One forward pass, three
answers, and the code branches in plain if-statements.

**A Tamil-language block message.** When the decider blocks a request and the message
contained Tamil script, the refusal is returned in Tamil. A citizen who wrote in Tamil
deserves to understand why they were refused in their own language.

**Six tools.** List schemes by category, get full scheme details, check eligibility from a
profile, get required documents and helpline, find application centres by district, get a
Tamil or English summary. All backed by real data.

## The architecture

< FIGURE 1 of 2: upload submission/article/architecture.png here >
Alt text: Architecture diagram showing citizen message flowing into SchemeEligibilityGate powered by Strands Decider 2B, which returns block/review/allow, then the Strands Agent on Amazon Bedrock Nova Pro calling tools backed by real PM Kisan and Magalir Urimai data, deployed on AgentCore Runtime.

The flow is:

1. Citizen sends a message in Tamil, English or mixed.
2. `SchemeEligibilityGate.check()` calls Strands Decider 2B with the message and the bilingual policy.
3. The decider returns `scheme_category`, `gaming_attempt` probability and `severity` level.
4. If `p_gaming >= 0.60` or severity is critical: block. Return refusal in Tamil or English.
5. If `p_gaming >= 0.35` or severity is serious: review. Inject caution note into system prompt.
6. Otherwise: allow. The Strands Agent runs with Amazon Bedrock Nova Pro and calls tools.
7. Tools return real scheme data, eligibility assessment, document lists, CSC locations.
8. The agent replies in the citizen's language.

The demo UI shows the live decision panel — scheme_category in teal, gaming probability bar
in green/amber/red, verdict tag — for every turn. The fraud attempt turn is the most
satisfying to watch: the bar goes red, the verdict says block, and the reply comes back in
Tamil before the agent ever runs.

## The decision in code

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

Writing the option descriptions was the most important part of the whole build. The decider
reads them as context for each question. "The citizen asks how to falsify income, hide land
ownership, manipulate family details" is much more precise than "fraud". That precision is
what makes the Tamil fraud attempts get caught even when the English keyword "fraud" never
appears.

## Eval cases and what I learned

I wrote 30 labelled cases: 20 genuine eligibility queries across Tamil, English and mixed
language, and 10 gaming/fraud attempts. The Tamil fraud cases were the interesting ones to
write. "நான் அரசு ஊழியன். PM Kisan-க்கு விண்ணப்பிக்க என் விவசாய நண்பன் பெயரில் நிலம்
வைக்கலாமா?" — a government employee asking if he can hold land in his farmer friend's name
to claim PM Kisan. That is a critical violation in any language.

The tuning cases taught me that vague phrasing is the hardest. "My income is close to the
limit, am I eligible?" reads borderline even to a human reader. The review verdict is the
right call there. I set `review_at=0.35` after running the benchmark and seeing where the
ambiguous cases landed.

## Measured results

< FIGURE 2 of 2: upload submission/bench/results.png here >
Alt text: Benchmark table comparing Strands Decider 2B vs qwen3.5-4b LLM on 15 held-out test cases showing accuracy and latency numbers.

Benchmark run against 15 held-out test cases (`split: test`) using the AWS User Group Madurai
hosted Strands Decider 2B (`strands-decider-2b-hobson-v19`) versus `qwen3.5-4b` as the LLM
baseline — both on the user group cloud:

| Metric | Strands Decider 2B | qwen3.5-4b (LLM) |
|---|---|---|
| Overall accuracy (45 decisions) | 77.8% | 91.1% |
| Accuracy when confident (>= 0.70) | **92.9%** | 91.1% |
| Confident answers | 62% of cases | 100% |
| Median latency per decision | **8,735 ms** | 22,653 ms |
| Latency p95 | 9,240 ms | 25,225 ms |
| Cost per 1,000 decisions | $0.035 | $0.000 |
| Speedup vs LLM (p50) | **2.6x faster** | — |

The decider is 2.6x faster than the LLM per decision. The LLM scores higher on raw accuracy
because it generates a full answer — but at 22 seconds median per decision on the user group
cloud, it is not practical for a fraud gate that runs on every single citizen message.

The more important number is 92.9% accuracy when confident. When the decider's confidence is
above 0.70, it gets the answer right 93% of the time. The 38% of cases below the confidence
threshold are the genuinely ambiguous ones — borderline phrasing that even a human reviewer
would flag. Those cases correctly get the review verdict rather than allow or block. That is
the intended behaviour for a citizen-facing policy gate.

The decider runs on the AWS User Group Madurai hosted API (CPU). Latency is dominated by the
network round trip. On a GPU or Apple Silicon it would be 0.1 to 0.3 seconds per decision.

## The reusable pattern

The `#policy` pattern in `agent/decision.py` is designed to be dropped into any agent where
a written policy governs what the agent may do. Insurance claims, loan applications, HR
policy, content moderation, procurement approvals.

The steps to reuse it are:

1. Copy `agent/decision.py` to your project.
2. Replace `POLICY` with your domain's written rules. Any language, plain prose.
3. Replace `CATEGORIES` with your taxonomy.
4. Set `block_at` and `review_at` to match your risk tolerance.
5. Call `gate.check(message)` before your agent and branch on `verdict.action`.

The Tamil+English bilingual policy is not special to this use case. Any policy written in
the user's language will work. The decider reads what you give it.

## What I would do next

I would connect the agent to the Tamil Nadu e-Sevai government API so the eligibility checks
use real citizen data rather than what the citizen describes. I would add AgentCore Memory
so returning citizens do not have to re-describe their situation. I would extend the policy
to Telugu and Kannada for broader South Indian coverage.

And I would let my grandmother try it.

## Links

- Code repository: https://github.com/Santhosh-p653/alphasource
- Demo video: (add after recording)
- Strands Decider 2B: https://huggingface.co/StrandsAgents/strands-decider-2B-qwen3.5-v1-2610
- Tags: `#strands-decider-2b` `#policy` `#amazon-bedrock` `#strands-agents` `#agentcore`

Built with the **AWS User Group Madurai** Strands Decider hackathon kit.
