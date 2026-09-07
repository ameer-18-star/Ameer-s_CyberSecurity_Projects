# ScopeSentry

A WiFi *defensive* monitoring and engagement-authorization toolkit.

ScopeSentry is **not** an attack tool. There is no offensive module in
this project: nothing here builds a `reaver`, `aireplay-ng`,
`hcxdumptool`, `bully`, or `hashcat` command, and nothing transmits a
deauthentication frame. What it does:

- **Engagement tracking** (`core/engagement.py`) — load a manifest
  (authorized BSSIDs + a time window) and answer "is this target currently
  authorized?" Standalone authorization bookkeeping, useful even outside
  this project.
- **Hash-chained evidence log** (`core/evidence_log.py`) — append-only,
  tamper-evident logging.
- **Passive recon** (`core/scanner.py`) — parses `airodump-ng` CSV output
  into a list of observed APs. Read-only; no `--bssid`/`-c` lock paired
  with an injection tool.
- **Defense monitors** (`core/defense/`):
  - `deauth_monitor.py` — passively counts deauth/disassoc frames via
    `tshark` and flags abnormal rates against *your own* baseline APs
    (detects someone else attacking your network).
  - `rogue_ap_monitor.py` — evil-twin / BSSID-mismatch / encryption- and
    channel-mismatch detection against a baseline you define.
  - `hardening_audit.py` — read-only checklist (weak encryption, WPS
    enabled) for your own baseline APs.
- **GUI** (`gui/`) — Dashboard, Engagement, Defense, Evidence, Results,
  Logs, and Settings tabs (PyQt6), wired together in `gui/main_window.py`.

## Requirements

```bash
pip install -r requirements.txt
# System tools used by core/ (all passive/observational):
#   iw, airmon-ng/airodump-ng (aircrack-ng package), tshark (wireshark-common)
```

## Running

```bash
python app.py --iface wlan0mon
```

## Running tests

```bash
export QT_QPA_PLATFORM=offscreen   # only needed in headless environments
pytest -q
```

## Packaging

See `packaging/README.md`.