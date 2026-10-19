#!/usr/bin/env python3
"""Kironomics session reporter - reads Kiro's state.vscdb and sends to the backend."""
import os, sys, ssl, json, sqlite3, urllib.request, urllib.error, time
from pathlib import Path

API_KEY = "85f15ef66d7b345934b570117507c82f57d17dd10b90b4068ab93830e7deaa39"
API_BASE = "https://2q4zt5zl9e.execute-api.us-east-1.amazonaws.com/dev"

COUNTER_DIR = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp")))

def read_int(path, default=0):
    try:
        return int(Path(path).read_text().strip())
    except Exception:
        return default

tools   = read_int(COUNTER_DIR / "kironomics_tools")
prompts = read_int(COUNTER_DIR / "kironomics_prompts")
start   = read_int(COUNTER_DIR / "kironomics_start", int(time.time()))
elapsed = max(0, int(time.time()) - start)

# Read Kiro's state.vscdb (silent fail if missing or no usageState)
plan_data = {}
try:
    home = Path.home()
    if sys.platform == "darwin":
        db = home / "Library/Application Support/Kiro/User/globalStorage/state.vscdb"
    elif sys.platform.startswith("win"):
        db = Path(os.environ.get("APPDATA", str(home / "AppData/Roaming"))) / "Kiro/User/globalStorage/state.vscdb"
    else:
        db = home / ".config/Kiro/User/globalStorage/state.vscdb"
    if db.exists():
        conn = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
        row = conn.execute(
            "SELECT value FROM ItemTable WHERE key=?",
            ("kiro.kiroAgent",),
        ).fetchone()
        conn.close()
        if row:
            state = json.loads(row[0])
            usage = state.get("kiro.resourceNotifications.usageState", {})
            breakdowns = usage.get("usageBreakdowns", [])
            if breakdowns:
                bd = breakdowns[0]
                plan_data = {
                    "currentUsage":    bd.get("currentUsage"),
                    "usageLimit":      bd.get("usageLimit"),
                    "percentageUsed":  bd.get("percentageUsed"),
                    "resetDate":       bd.get("resetDate"),
                }
except Exception:
    pass

payload = {
    "token":           API_KEY,
    "tool_calls":      tools,
    "prompts":         prompts,
    "elapsed_seconds": elapsed,
    **plan_data,
}

def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return None

try:
    req = urllib.request.Request(
        f"{API_BASE}/kironomics/session",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5, context=_ssl_context()).read()
    except (ssl.SSLError, urllib.error.URLError) as e:
        if "certificate verify failed" in str(e).lower():
            urllib.request.urlopen(req, timeout=5, context=ssl._create_unverified_context()).read()
        else:
            raise
except Exception:
    pass

# Cleanup temp counters
for f in ["kironomics_tools", "kironomics_prompts", "kironomics_start"]:
    try:
        (COUNTER_DIR / f).unlink()
    except Exception:
        pass
