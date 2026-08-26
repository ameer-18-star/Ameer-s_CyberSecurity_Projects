# Educational Keylogger Demo
> **For internship / cybersecurity awareness purposes only.**
> Run only on your own machine. Never deploy on systems you don't own.

---

## What it does
| Feature | Detail |
|---|---|
| Keystroke capture | Records every key press & release using `pynput` |
| Log file | Saved to `~/Desktop/keylog_session.txt` (human-readable) |
| JSON file | Saved to `~/Desktop/keylog_session.json` (structured data) |
| Web dashboard | Live browser UI at `http://localhost:5000` |
| Auto-stop | Stops cleanly on `Ctrl+C` or OS shutdown |
| Fully offline | No data ever leaves your machine |

---

## Setup

### 1 — Install Python (3.8+)
Download from https://python.org if not already installed.

### 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### 3 — Run
```bash
python keylogger.py
```

### 4 — Open dashboard
Visit **http://localhost:5000** in your browser.

### 5 — Stop
Press `Ctrl + C` in the terminal.

---

## Project structure
```
keylogger_demo/
├── keylogger.py          ← Main Python script (keylogger + Flask server)
├── requirements.txt      ← pip dependencies
├── README.md             ← This file
└── templates/
    └── dashboard.html    ← Browser dashboard (HTML/CSS/JS)
```

---

## How the keylogger works (internship presentation notes)
1. **pynput** registers OS-level keyboard listeners (works on Windows, macOS, Linux).
2. `on_press` and `on_release` callbacks fire for every key event.
3. Each event is timestamped, labeled, and appended to a log file.
4. Flask serves the in-memory event list via a JSON REST API (`/api/events`, `/api/stats`).
5. The browser polls the API every second and re-renders the feed — all local, no internet.

## Security protection tips (to include in your presentation)
- Use **anti-malware / EDR** software
- Use a **password manager** with auto-fill (keys are never typed)
- Use **virtual on-screen keyboard** for sensitive input
- Enable **2FA / MFA** on all accounts
- Keep **OS and software updated**
- Never run **unknown executables or attachments**
