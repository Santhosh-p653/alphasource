"""Tamil Nadu Government Scheme Eligibility Gate.

A citizen-facing assistant for Tamil Nadu and South India. Before the agent
responds or calls any tool, Strands Decider 2B classifies the request:
  - genuine eligibility queries are allowed
  - borderline requests proceed with a caution note
  - fraud/gaming attempts are blocked before any tool runs

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("PM Kisan திட்டத்திற்கு நான் தகுதியானவனா?")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, image_blocks, strip_thinking

from .decision import SchemeEligibilityGate
from .tools import TOOLS

NAME = "Tamil Nadu Scheme Eligibility Gate"

SYSTEM_PROMPT = """You are a helpful government scheme assistant for citizens of Tamil Nadu and South India.
You help people understand and apply for welfare schemes like PM Kisan Samman Nidhi,
Kalaignar Magalir Urimai Thogai, TNPDS ration card, and other central and state programmes.

You can:
- Explain eligibility criteria in simple, plain language (English or Tamil)
- List required documents for any scheme
- Help citizens understand if they likely qualify based on what they tell you
- Find application centres and helpline numbers
- Summarise scheme benefits

Always be respectful and empathetic. Many users are from rural areas and may not be familiar
with government processes. Use simple words. When a user writes in Tamil, reply in Tamil.
When mixed, use both.

Important: your role is to inform and guide — not to advise on how to manipulate or falsify
any information. If something seems incorrect in what the user says, gently clarify."""

REVIEW_SUFFIX = (
    "\n\n[Policy note: this request has borderline phrasing. Answer only about genuine "
    "eligibility criteria and official application processes. Do not suggest any way to "
    "modify or present information differently to gain eligibility. Flag this case "
    "if the user persists with suspicious questions.]"
)

BLOCK_MESSAGES = {
    "en": (
        "I cannot help with that. This assistant is here to help citizens understand "
        "government scheme eligibility honestly. Attempting to falsify income, land records "
        "or family details to claim benefits is a punishable offence under Indian law. "
        "If you have a genuine eligibility question, please ask and I will be happy to help."
    ),
    "ta": (
        "மன்னிக்கவும், இதற்கு நான் உதவ முடியாது. இந்த உதவியாளர் அரசு திட்டங்களில் "
        "உண்மையான தகுதி கேள்விகளுக்கு மட்டுமே உதவும். வருமானம் அல்லது நிலம் பற்றிய "
        "தகவல்களை திரிபுபடுத்துவது இந்திய சட்டத்தின் கீழ் தண்டனைக்குரிய குற்றம். "
        "உண்மையான தகுதி கேள்வி இருந்தால் கேளுங்கள், உதவுகிறேன்."
    ),
}


def _detect_tamil(message: str) -> bool:
    """Return True if the message contains Tamil script characters."""
    return any("\u0B80" <= c <= "\u0BFF" for c in message)


class HackathonAgent:
    """One Strands agent per session, with the SchemeEligibilityGate before every turn."""

    def __init__(
        self,
        decider: Decider | None = None,
        model_id: str | None = None,
        eager: bool | None = None,
    ):
        import os

        self.decider = decider or Decider()
        self.eager = eager if eager is not None else os.environ.get("DEMO_EAGER") == "1"
        self.model_id = model_id or default_model_id()
        self.gate = SchemeEligibilityGate(self.decider)
        self.sessions: dict[str, Agent] = {}

    def _session(self, session_id: str, system_prompt: str) -> Agent:
        if session_id not in self.sessions:
            self.sessions[session_id] = Agent(
                model=agent_model(self.model_id),
                system_prompt=system_prompt,
                tools=TOOLS,
                callback_handler=None,
            )
        return self.sessions[session_id]

    def chat(
        self,
        message: str,
        session_id: str = "default",
        images: list[Any] | None = None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        before = len(self.gate.log)

        verdict = self.gate.check(message)

        if verdict.action == "block":
            lang = "ta" if _detect_tamil(message) else "en"
            return {
                "reply": BLOCK_MESSAGES[lang],
                "decisions": self.gate.log[before:],
                "model_id": self.model_id,
                "latency_ms": round((time.perf_counter() - t0) * 1000),
                "agent": NAME,
                "eager": self.eager,
            }

        system_prompt = SYSTEM_PROMPT + (REVIEW_SUFFIX if verdict.action == "review" else "")
        agent = self._session(session_id, system_prompt)

        result = agent(
            [*image_blocks(images), {"text": message}] if images else message,
            invocation_state={"images": list(images or [])},
        )
        reply = strip_thinking(str(result))

        return {
            "reply": reply,
            "decisions": self.gate.log[before:],
            "model_id": self.model_id,
            "latency_ms": round((time.perf_counter() - t0) * 1000),
            "agent": NAME,
            "eager": self.eager,
        }


if __name__ == "__main__":
    import json, sys

    a = HackathonAgent()
    for msg in sys.argv[1:] or [
        "PM Kisan திட்டத்திற்கு நான் தகுதியானவனா? என்னிடம் 2 ஏக்கர் நிலம் உள்ளது.",
        "What documents do I need for Kalaignar Magalir Urimai Thogai?",
        "நான் ஒரு விவசாயி. PM Kisan-க்கு விண்ணப்பிக்க என்ன செய்ய வேண்டும்?",
        "How can I show lower income so I qualify for Magalir Urimai even though my family earns more?",
    ]:
        print(f"\n>>> {msg}")
        out = a.chat(msg)
        print(json.dumps({k: v for k, v in out.items() if k != "decisions"}, indent=2))
        for d in out["decisions"]:
            print("  decision:", json.dumps(d))
