# Tamil Nadu Government Scheme Eligibility Gate

- **Pitch:** a citizen-facing assistant that helps people in Tamil Nadu and South India discover
  and check eligibility for government welfare schemes — in Tamil, English, or both — while
  Strands Decider 2B classifies every request before the agent acts, blocking attempts to
  game the system and flagging ambiguous queries for human review.
- **Who it is for:** citizens of Tamil Nadu and other South Indian states seeking information
  about government schemes such as PM Kisan Samman Nidhi, Kalaignar Magalir Urimai Thogai
  (women's welfare cash transfer), TNPDS ration card services, and other central and state
  welfare programmes. Especially useful for rural citizens who communicate in Tamil.
- **Features:**
  - answers eligibility questions across five scheme categories: agriculture, women_welfare,
    ration_food, education_youth, and housing_infrastructure;
  - accepts requests in Tamil, English, Telugu, Kannada, or a mix;
  - every request is classified by Strands Decider 2B before the agent responds or calls
    any tool — allow, review, or block;
  - blocks attempts to fraudulently claim benefits the citizen is not eligible for;
  - flags ambiguous requests (e.g. "how do I show lower income") for human review rather
    than silently helping or blocking;
  - explains eligibility criteria in plain language, not bureaucratic prose;
  - lists required documents and nearest application centres by district;
  - deployed on Amazon Bedrock AgentCore Runtime.
- **The decision handed to Strands Decider 2B:** before the agent responds to any citizen
  request, classify the request into a scheme category and determine whether it is a genuine
  eligibility query, an attempt to game or falsify eligibility, or a borderline case that needs
  human review. (`#policy`)
- **Why a decision model:** eligibility rules are written in prose ("annual family income below
  Rs 2 lakh", "must be a Tamil Nadu resident for at least 5 years", "woman aged 21 to 60 with
  Aadhaar-linked bank account"). Those are language-level policy rules, not arithmetic. A regex
  filter cannot detect "tell me how to show I own less land so I qualify" in Tamil. Strands
  Decider 2B returns calibrated probabilities in one forward pass — no second LLM call needed.
- **Real data used:**
  - PM Kisan Samman Nidhi: official eligibility, benefit amount, application process
    (source: pmkisan.gov.in)
  - Kalaignar Magalir Urimai Thogai: official eligibility, Rs 1,000/month benefit, required
    documents (source: cms.tn.gov.in)
- **Amazon Bedrock:** the conversation and eligibility explanation (Amazon Nova Pro by default).
