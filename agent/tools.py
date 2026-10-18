"""Developer Policy Gate tools: mock data for a developer productivity assistant.

Each tool represents a capability the agent can use after the policy gate allows the request.
Mock data is in-memory so the demo runs anywhere without external dependencies.
"""

from __future__ import annotations

from strands import tool

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

SNIPPETS = {
    "python_http": {
        "language": "python",
        "title": "HTTP GET with requests",
        "code": (
            "import requests\n"
            "response = requests.get('https://api.example.com/data')\n"
            "response.raise_for_status()\n"
            "data = response.json()\n"
            "print(data)"
        ),
        "tags": ["python", "http", "requests"],
    },
    "python_env": {
        "language": "python",
        "title": "Read environment variables",
        "code": (
            "import os\n"
            "from dotenv import load_dotenv\n\n"
            "load_dotenv()\n"
            "api_key = os.getenv('API_KEY', 'default-value')\n"
            "print(api_key)"
        ),
        "tags": ["python", "environment", "dotenv"],
    },
    "git_branch": {
        "language": "bash",
        "title": "Git: create and switch branch",
        "code": (
            "git checkout -b feature/my-feature\n"
            "# make your changes, then:\n"
            "git add .\n"
            "git commit -m 'feat: add my feature'\n"
            "git push -u origin feature/my-feature"
        ),
        "tags": ["git", "branch", "workflow"],
    },
    "docker_run": {
        "language": "bash",
        "title": "Docker: build and run a container",
        "code": (
            "# Build the image\n"
            "docker build -t my-app:latest .\n\n"
            "# Run with environment variables and port mapping\n"
            "docker run -d -p 8080:8080 \\\n"
            "  -e DATABASE_URL=postgres://localhost/mydb \\\n"
            "  --name my-app my-app:latest"
        ),
        "tags": ["docker", "container", "devops"],
    },
}

DOCS = {
    "onboarding": {
        "title": "Developer Onboarding Guide",
        "sections": ["Repository setup", "Local dev environment", "Running tests", "PR workflow"],
        "summary": "Step-by-step guide to get a new developer productive in under a day.",
    },
    "api_reference": {
        "title": "Internal API Reference",
        "sections": ["Authentication", "Endpoints", "Rate limits", "Error codes"],
        "summary": "REST API reference for the internal platform services.",
    },
    "runbook": {
        "title": "Production Runbook",
        "sections": ["Deployments", "Rollbacks", "Incident response", "On-call checklist"],
        "summary": "Runbook for on-call engineers: deployments, incidents and rollbacks.",
    },
}

TASKS: list[dict] = [
    {"id": "T-101", "title": "Migrate auth service to OAuth2", "status": "in_progress", "priority": "high", "assignee": "dev1"},
    {"id": "T-102", "title": "Write unit tests for payment module", "status": "open", "priority": "medium", "assignee": None},
    {"id": "T-103", "title": "Update Python dependencies", "status": "open", "priority": "low", "assignee": None},
    {"id": "T-104", "title": "Fix N+1 query in user dashboard", "status": "open", "priority": "high", "assignee": "dev2"},
    {"id": "T-105", "title": "Document deployment process", "status": "done", "priority": "medium", "assignee": "dev1"},
]

DEBUG_KB = {
    "import_error": "Check that the package is listed in requirements.txt and the venv is activated.",
    "connection_refused": "Verify the service is running (docker ps / systemctl status) and the port matches.",
    "permission_denied": "The process lacks read/write access. Check file permissions (ls -la) or run with sudo if appropriate.",
    "memory_error": "Profile with memory_profiler or tracemalloc. Look for large in-memory lists or unclosed file handles.",
    "timeout": "Increase the client timeout, add retries with exponential back-off, or move the work to a background job.",
}

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def search_code_snippets(query: str) -> dict:
    """Search the internal snippet library for reusable code examples matching a query."""
    q = query.lower()
    results = [
        {"id": sid, **s}
        for sid, s in SNIPPETS.items()
        if q in s["title"].lower() or any(q in t for t in s["tags"])
    ]
    return {"query": query, "results": results, "count": len(results)}


@tool
def get_code_snippet(snippet_id: str) -> dict:
    """Retrieve a specific code snippet by its id (e.g. python_http, git_branch)."""
    s = SNIPPETS.get(snippet_id)
    if not s:
        return {"error": f"No snippet with id '{snippet_id}'. Use search_code_snippets to find one."}
    return {"id": snippet_id, **s}


@tool
def list_documentation(topic: str = "") -> dict:
    """List available internal documentation pages, optionally filtered by topic keyword."""
    t = topic.lower()
    results = {
        did: {"title": d["title"], "summary": d["summary"]}
        for did, d in DOCS.items()
        if not t or t in d["title"].lower() or any(t in s.lower() for s in d["sections"])
    }
    return {"topic": topic or "all", "documents": results}


@tool
def get_documentation(doc_id: str) -> dict:
    """Retrieve a documentation page by its id (e.g. onboarding, api_reference, runbook)."""
    d = DOCS.get(doc_id)
    if not d:
        return {"error": f"No document '{doc_id}'. Use list_documentation to find one."}
    return {"id": doc_id, **d}


@tool
def list_tasks(status: str = "", priority: str = "") -> dict:
    """List project tasks, optionally filtered by status (open/in_progress/done) or priority (low/medium/high)."""
    results = [
        t for t in TASKS
        if (not status or t["status"] == status)
        and (not priority or t["priority"] == priority)
    ]
    return {"filters": {"status": status, "priority": priority}, "tasks": results, "count": len(results)}


@tool
def get_debug_hint(error_type: str) -> dict:
    """Get a debugging hint for a known error type (import_error, connection_refused, permission_denied, memory_error, timeout)."""
    hint = DEBUG_KB.get(error_type.lower().replace(" ", "_"))
    if not hint:
        available = list(DEBUG_KB.keys())
        return {"error": f"No hint for '{error_type}'.", "available": available}
    return {"error_type": error_type, "hint": hint}


TOOLS = [
    search_code_snippets,
    get_code_snippet,
    list_documentation,
    get_documentation,
    list_tasks,
    get_debug_hint,
]
