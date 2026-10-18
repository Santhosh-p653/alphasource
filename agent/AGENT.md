# Developer Policy Gate

- **Pitch:** a productivity assistant for developers that classifies every incoming request
  through Strands Decider 2B before acting — so the agent never executes a risky, out-of-scope
  or policy-violating task. Supports requests in English and Tamil (தமிழ்).
- **Who it is for:** software developers using an AI assistant for day-to-day productivity tasks
  such as code generation, documentation, debugging help, and project management queries.
  Especially useful for Tamil-speaking developer teams who work in a bilingual environment.
- **Features:**
  - answers developer questions across five categories: code, documentation, debugging,
    project management, and general productivity;
  - accepts requests in English, Tamil, or a mix of both;
  - every request is classified by Strands Decider 2B before the agent responds or acts;
  - high-risk or policy-violating requests are blocked with a clear explanation;
  - borderline requests are flagged for review rather than silently allowed or silently blocked;
  - a live decision panel in the demo UI shows the category, violation probability and verdict
    for every turn;
  - deployed on Amazon Bedrock AgentCore Runtime.
- **The decision handed to Strands Decider 2B:** before the agent acts on any developer
  request, classify the request into a policy category and determine whether it violates the
  developer productivity policy (allow / review / block). (`#policy`)
- **Why a decision model:** policy classification needs language understanding — what the
  developer actually meant, whether a request crosses a line written in prose, which category
  fits. A regex or keyword filter cannot do it reliably. Strands Decider 2B returns calibrated
  probabilities the code can branch on, in a single fast forward pass.
- **Amazon Bedrock:** the conversation, code generation and tool use (Amazon Nova Pro by
  default).
