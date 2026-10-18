"""REUSABLE DECISION PATTERN: government scheme eligibility policy gate  (#policy)

What it does
    Before the citizen-facing agent responds to any request about government welfare schemes,
    Strands Decider 2B reads the citizen's message and classifies it against the scheme
    assistance policy:

    - Which scheme category does the request fall under?
      (agriculture, women_welfare, ration_food, education_youth, housing_infrastructure)
    - Does the request attempt to game or falsify eligibility?
      (e.g. "help me show I own less land", "how do I hide my income to qualify")
    - How severe would it be to act on this request?

    Genuine eligibility queries are allowed. Borderline or ambiguous requests are flagged for
    human review. Requests that attempt to fraudulently obtain benefits are blocked before the
    agent runs.

Typed questions and options
    scheme_category (choice):
        agriculture            — PM Kisan, crop insurance, farmer welfare
        women_welfare          — Magalir Urimai Thogai, women empowerment schemes
        ration_food            — TNPDS ration card, subsidised food, PDS
        education_youth        — scholarship, student welfare, skill development
        housing_infrastructure — PMAY housing, rural infrastructure, MGNREGS

    gaming_attempt (noul):
        true  — the request asks the agent to help falsify, hide or manipulate information
                to fraudulently qualify for a scheme; or asks how to exploit loopholes to
                claim benefits the citizen is not eligible for under the written rules
        false — the request is a genuine eligibility query, a request for information about
                a scheme, or help understanding the application process

    severity (score) — ["none", "minor", "serious", "critical"]:
        none     — a genuine, harmless eligibility or information query
        minor    — vague or slightly suspicious phrasing but likely benign intent
        serious  — explicitly asks how to manipulate income, land or family records
        critical — explicit fraud request: asking the agent to help falsify documents or
                   submit false information to obtain government benefits

Wiring
    `SchemeEligibilityGate` is called in `HackathonAgent.chat()` BEFORE the Strands Agent:

        gate = SchemeEligibilityGate(decider)
        verdict = gate.check(message)
        if verdict.action == "block":
            return early reply explaining the request cannot be helped
        if verdict.action == "review":
            add a note to the system prompt to answer carefully and flag the case

    The gate appends one log record per check to `.log`: scheme_category, p_gaming,
    severity, verdict and decider_ms. `chat()` copies these into the `decisions` list.

How to reuse it in your own agent
    1. Copy this file into your agent directory.
    2. Replace POLICY with your own written policy (plain prose, any language).
    3. Replace CATEGORIES with your scheme or domain taxonomy (2-8 options).
    4. Adjust block_at and review_at thresholds in SchemeEligibilityGate.__init__.
    5. Call gate.check(user_message) before your agent runs; branch on verdict.action.
    Works for any domain where a written policy governs what the agent may help with.
"""

from __future__ import annotations

from typing import Any

from decider_kit import Decider
from decider_kit.patterns.policy import PolicyCheck, Verdict

PATTERN_TAG = "#policy"

# ---------------------------------------------------------------------------
# Policy text — English + Tamil
# ---------------------------------------------------------------------------

POLICY = (
    "This assistant helps citizens of Tamil Nadu and South India understand and apply for "
    "government welfare schemes such as PM Kisan Samman Nidhi, Kalaignar Magalir Urimai "
    "Thogai, TNPDS ration card, and related programmes. Requests may be in English, Tamil, "
    "Telugu, Kannada, or a mix; the language does not affect the policy. "
    "The assistant MAY: explain eligibility rules in plain language; list required documents; "
    "help citizens understand whether they meet the criteria based on information they provide; "
    "find application centres and helpline numbers. "
    "The assistant must NOT: help citizens falsify, hide or manipulate income, land ownership, "
    "family composition, employment status or any other information to fraudulently qualify "
    "for a scheme; suggest ways to exploit loopholes to claim benefits they are not entitled "
    "to; or help submit false information to government portals. "
    # Tamil policy text
    "தமிழ் விதிமுறைகள்: இந்த உதவியாளர் அரசு திட்டங்களில் தகுதி பற்றிய உண்மையான "
    "கேள்விகளுக்கு மட்டுமே உதவும். வருமானம், நிலம் அல்லது குடும்ப விவரங்களை "
    "திரிபுபடுத்தி தகுதி பெற முயற்சிப்பது தடைசெய்யப்பட்டது. "
    "தேவையான ஆவணங்கள் மற்றும் விண்ணப்ப நடைமுறைகளில் உதவலாம்."
)

# ---------------------------------------------------------------------------
# Scheme categories
# ---------------------------------------------------------------------------

CATEGORIES = {
    "agriculture":             "PM Kisan, crop insurance, farmer welfare and agriculture-related schemes",
    "women_welfare":           "Magalir Urimai Thogai, women empowerment, self-help group schemes",
    "ration_food":             "TNPDS ration card, subsidised food, Public Distribution System",
    "education_youth":         "scholarship, student welfare, skill development, youth employment",
    "housing_infrastructure":  "PMAY housing, rural infrastructure, MGNREGS, sanitation schemes",
}

# ---------------------------------------------------------------------------
# Typed questions (used by the benchmark)
# ---------------------------------------------------------------------------

QUESTIONS = {
    "scheme_category": Decider.choice(
        "Which government scheme category does this citizen request fall under?",
        CATEGORIES,
    ),
    "gaming_attempt": Decider.noul(
        f"Does this request attempt to game or fraudulently obtain government scheme benefits? "
        f"Policy: {POLICY}",
        {
            "true":  "the citizen is asking how to falsify income records, hide land ownership, "
                     "manipulate family details, or exploit loopholes to fraudulently qualify "
                     "for a scheme they are not genuinely entitled to",
            "false": "the citizen is asking a genuine question about eligibility, required "
                     "documents, application process, or scheme benefits",
        },
    ),
    "severity": Decider.score(
        "How serious is this request from a fraud-prevention standpoint?",
        ["none", "minor", "serious", "critical"],
    ),
}


# ---------------------------------------------------------------------------
# Wiring class
# ---------------------------------------------------------------------------

class SchemeEligibilityGate:
    """Policy gate for government scheme eligibility requests.

    Call check(message) before the agent runs. Branch on verdict.action:
        'allow'  — genuine query; agent proceeds normally
        'review' — borderline; agent proceeds with caution note in system prompt
        'block'  — gaming/fraud attempt; return refusal, do not invoke agent
    """

    def __init__(
        self,
        decider: Decider | None = None,
        block_at: float = 0.60,
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
        """Classify `message` and return a Verdict with action, scheme_category, p_gaming, severity."""
        verdict = self._check.check(message, context=session_context)
        if self.log:
            self.log[-1]["verdict"] = verdict.action
            self.log[-1]["pattern"] = PATTERN_TAG
        return verdict
