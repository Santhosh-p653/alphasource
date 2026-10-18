# Video Narration Script — Tamil Nadu Scheme Eligibility Gate

## 0. Title card

Tamil Nadu Government Scheme Eligibility Gate. Built on Amazon Bedrock with Strands Decider 2B
for policy classification. Every citizen request is classified before the agent acts — one
forward pass, three typed answers, no second LLM call.

## 1. Features slide

This assistant helps citizens of Tamil Nadu discover and apply for government welfare schemes.
It supports Tamil, English and mixed-language requests. It explains PM Kisan Samman Nidhi
and Kalaignar Magalir Urimai Thogai in plain language, lists required documents, finds
application centres by district, and checks whether a citizen likely qualifies. Before every
response, Strands Decider 2B classifies the request: genuine query, borderline, or fraud attempt.

## 2. Turn 1 — Tamil farmer asking about PM Kisan (ALLOW)

A Tamil farmer from Madurai asks about PM Kisan eligibility in Tamil. Watch the decision panel
on the right. The decider classifies the request as agriculture, returns a low gaming attempt
probability, and the verdict is allow. The agent replies with the eligibility criteria and
next steps in Tamil. This is what the assistant is built for.

## 3. Turn 2 — Documents for Magalir Urimai (ALLOW)

A family asks in English what documents they need for Kalaignar Magalir Urimai Thogai. The
decider classifies it as women welfare, gaming attempt probability is near zero, verdict is
allow. The agent lists the required documents and the helpline number. Real data from the
official Tamil Nadu government portal.

## 4. Turn 3 — Find application centre in Coimbatore (ALLOW)

A citizen asks where to apply for PM Kisan in Coimbatore. Decider allows it. The agent
returns the Common Service Centre locations and explains which land documents to bring. No
hallucination — the data comes from the in-memory scheme database.

## 5. Turn 4 — Fraud attempt blocked (BLOCK)

Now watch what happens when someone asks how to show lower income to qualify for Magalir
Urimai. The decider catches this as a serious gaming attempt. The verdict is block. The
agent never runs. No tool is called. The refusal is returned in Tamil because the citizen
wrote in Tamil. One forward pass. Blocked before anything else happens.

## 6. Benchmark slide

The benchmark compares Strands Decider 2B against a Bedrock LLM asked the same questions on
the held-out test cases. The decider is faster and costs nothing on the free tier. The LLM
is more accurate on edge cases. For a fraud gate where speed and cost matter more than
marginal accuracy on ambiguous phrasing, the decider wins clearly.

## 7. End card

Tamil Nadu Scheme Eligibility Gate. The reusable policy pattern is in agent/decision.py.
Drop it into any agent where a written policy governs what the agent may do. Any language,
plain prose. See the repository and the Builder Center article for the full story.
Built with the AWS User Group Madurai Strands Decider hackathon kit.
