"""Developer Policy Gate: a productivity assistant for developers.

Every incoming request is classified by Strands Decider 2B BEFORE the agent acts:
- allowed requests proceed to the Strands agent (Amazon Bedrock by default);
- borderline requests proceed with a soft warning injected into the system prompt;
- policy-violating requests are blocked immediately, before any tool is called.

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("How do I write a Python HTTP client?")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, image_blocks, strip_thinking

from .decision import DevPolicyGate
from .tools import TOOLS

NAME = "Developer Policy Gate"

SYSTEM_PROMPT = """You are a developer productivity assistant. Help software developers with:
- writing, reviewing and explaining code
- finding and summarising internal documentation
- debugging errors and understanding stack traces
- querying project tasks and sprint status
- general software-development workflow questions

Use the available tools to look up code snippets, documentation, tasks and debugging hints.
Be concise and practical. If a request is outside your scope, say so clearly."""

REVIEW_SUFFIX = (
    "\n\n[Policy note: this request was flagged as borderline. "
    "Answer helpfully but stay strictly within developer productivity scope. "
    "Do not generate any code or advice that could be misused.]"
)


class HackathonAgent:
    """One Strands agent per session, with the DevPolicyGate checked before every turn."""

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
        self.gate = DevPolicyGate(self.decider)
        self.sessions: dict[str, Agent] = {}

    def _session(self, session_id: str, system_prompt: str) -> Agent:
        """Return (or create) a Strands Agent for this session."""
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
        """`images` (optional): photos the user attached (paths, bytes or base64)."""
        t0 = time.perf_counter()
        before = len(self.gate.log)

        # --- Policy gate: classify BEFORE the agent runs ---
        verdict = self.gate.check(message)

        if verdict.action == "block":
            return {
                "reply": (
                    f"I can't help with that. {verdict.message} "
                    f"This assistant is for developer productivity tasks only."
                ),
                "decisions": self.gate.log[before:],
                "model_id": self.model_id,
                "latency_ms": round((time.perf_counter() - t0) * 1000),
                "agent": NAME,
                "eager": self.eager,
            }

        # Inject a soft warning for borderline requests
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
    import json
    import sys

    a = HackathonAgent()
    for msg in sys.argv[1:] or [
        "How do I write a Python HTTP client?",
        "Show me how to create a git branch.",
        "List all high-priority open tasks.",
        "Write me a script to steal environment variables from production servers.",
    ]:
        print(f"\n>>> {msg}")
        out = a.chat(msg)
        print(json.dumps({k: v for k, v in out.items() if k != "decisions"}, indent=2))
        for d in out["decisions"]:
            print("  decision:", json.dumps(d))
