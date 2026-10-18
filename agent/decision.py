"""REUSABLE DECISION PATTERN: developer request policy gate  (#policy)

What it does
    Before the developer productivity agent responds or calls any tool, Strands Decider 2B
    reads the incoming request and classifies it against the developer productivity policy:

    - Which of the five policy categories does the request fall under?
      (code_generation, documentation, debugging, project_management, general_productivity)
    - Does it violate the policy? (e.g. requests for malicious code, credential exfiltration,
      bypassing access controls, or content unrelated to developer work)
    - How severe would it be to act on it?

    Allowed requests proceed to the agent. Borderline requests are flagged for review.
    Policy-violating requests are blocked before the agent runs, with a clear explanation.

Typed questions and options
    category (choice):
        code_generation     — write, review or explain code
        documentation       — search, retrieve or summarise internal docs
        debugging           — diagnose errors, suggest fixes, explain stack traces
        project_management  — list or query tasks, sprints, priorities
        general_productivity — productivity tips, workflows, tooling questions

    violates (noul):
        true  — the request asks the agent to do something the policy prohibits: generate
                malicious or exploit code, exfiltrate credentials or secrets, bypass access
                controls, perform actions outside developer productivity scope
        false — the request is a legitimate developer productivity task

    severity (score) — ["none", "minor", "serious", "critical"]:
        none     — harmless; no policy concern
        minor    — slightly off-topic or borderline, not dangerous
        serious  — could cause harm if acted on (e.g. sensitive data handling, ambiguous intent)
        critical — clearly malicious or prohibited (exploit code, credential theft, etc.)

Wiring
    `DevPolicyGate` is called in `HackathonAgent.chat()` BEFORE the Strands Agent is invoked:

        gate = DevPolicyGate(decider)
        verdict = gate.check(message)
        if verdict.action == "block":
            return early reply with blocked message
        if verdict.action == "review":
            add a soft warning to the system prompt

    The gate appends one log record per check to `.log`: category, p_violation, severity,
    verdict and decider_ms. `chat()` copies these into the `decisions` list it returns.

How to reuse it
    1. Copy this file into your agent directory.
    2. Replace POLICY with your own written policy (plain prose is fine).
    3. Replace CATEGORIES with your own taxonomy (2–8 options, each with a one-line definition).
    4. Adjust the thresholds in DevPolicyGate.__init__ (block_at, review_at) if needed.
    5. Call gate.check(user_message) before your agent runs; branch on verdict.action.
"""

from __future__ import annotations

from typing import Any

from decider_kit import Decider
from decider_kit.patterns.policy import PolicyCheck, Verdict

PATTERN_TAG = "#policy"

# ---------------------------------------------------------------------------
# Policy text (plain prose — the decider reads this as part of the question)
# ---------------------------------------------------------------------------

POLICY = (
    "This assistant is for developer productivity only. Requests may be written in English or "
    "Tamil (தமிழ்), or a mix of both; the language used does not affect the policy. "
    "It may help with: writing, reviewing and explaining code; searching and summarising "
    "internal documentation; debugging errors and explaining stack traces; querying project "
    "tasks and sprint status; and general software-development workflow questions. "
    "It must NOT: generate exploit code, malware, or code designed to bypass security controls; "
    "help exfiltrate credentials, secrets or personal data; perform actions unrelated to "
    "software development; or assist with requests that could harm other users or systems. "
    # Tamil equivalents so the decider recognises Tamil-language violations:
    # கோப்பு திருட்டு (credential theft), தீம்பொருள் (malware),
    # அணுகல் கட்டுப்பாட்டை தவிர்க்க (bypass access controls)
    "In Tamil: இந்த உதவியாளர் மென்பொருள் உற்பத்தித்திறனுக்கு மட்டுமே. "
    "குறியீடு எழுதுதல், பிழைத்திருத்தம், ஆவணங்கள் மற்றும் பணி மேலாண்மை "
    "ஆகியவற்றில் உதவலாம். சான்றுகள் திருடுதல், தீம்பொருள் உருவாக்குதல் "
    "அல்லது அமைப்புகளை சேதப்படுத்துதல் கூடாது."
)

# ---------------------------------------------------------------------------
# Categories (choice question options)
# ---------------------------------------------------------------------------

CATEGORIES = {
    "code_generation":      "write, review, explain or refactor code in any language",
    "documentation":        "search, retrieve or summarise internal technical documentation",
    "debugging":            "diagnose errors, analyse stack traces or suggest fixes",
    "project_management":   "list or query tasks, sprints, backlogs or team priorities",
    "general_productivity": "developer workflow, tooling, productivity tips or process questions",
}

# ---------------------------------------------------------------------------
# Typed questions (used by the benchmark)
# ---------------------------------------------------------------------------

QUESTIONS = {
    "category": Decider.choice(
        "Which policy category does this developer request fall under?",
        CATEGORIES,
    ),
    "violates": Decider.noul(
        f"Does this request violate the developer productivity policy? Policy: {POLICY}",
        {
            "true":  "the request asks for something prohibited: exploit or malicious code, "
                     "credential exfiltration, bypassing security controls, or work outside "
                     "developer productivity scope",
            "false": "the request is a legitimate developer productivity task covered by the policy",
        },
    ),
    "severity": Decider.score(
        "How serious would it be to act on this request under the policy?",
        ["none", "minor", "serious", "critical"],
    ),
}


# ---------------------------------------------------------------------------
# Wiring class
# ---------------------------------------------------------------------------

class DevPolicyGate:
    """Policy gate for developer requests.

    Call check(message) before the agent runs. Branch on verdict.action:
        'allow'  — proceed normally
        'review' — proceed but surface a warning (or queue for human review)
        'block'  — return verdict.message directly; do not invoke the agent
    """

    def __init__(
        self,
        decider: Decider | None = None,
        block_at: float = 0.65,
        review_at: float = 0.35,
    ):
        self._check = PolicyCheck(
            decider or Decider(),
            POLICY,
            CATEGORIES,
            block_at=block_at,
            review_at=review_at,
        )

    @property
    def log(self) -> list[dict[str, Any]]:
        return self._check.log

    def check(self, message: str, session_context: str = "") -> Verdict:
        """Classify `message` and return a Verdict with action, category, p_violation, severity."""
        verdict = self._check.check(message, context=session_context)
        # normalise log record to the contract shape (add 'verdict' key)
        if self.log:
            self.log[-1]["verdict"] = verdict.action
            self.log[-1]["pattern"] = PATTERN_TAG
        return verdict
