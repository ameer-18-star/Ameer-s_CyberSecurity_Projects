"""Passive recon: parse `airodump-ng`'s live CSV output into APRecord objects.

This only ever listens. It runs airodump-ng with no --bssid lock, no -c
channel lock tied to an attack, and never pairs it with aireplay-ng. The
output is informational — there is no "attack queue" anywhere downstream of
this module, because there is no attack engine in this project.
"""

from __future__ import annotations

import csv
import os
import subprocess
import time
from io import StringIO

from PyQt6.QtCore import QThread, pyqtSignal

from core.models import APRecord

_CLIENT_HEADER_MARKER = "Station MAC"

# airodump-ng's "Privacy" column sometimes still reports "WPA2" for networks
# that have actually moved to WPA3 (or WPA3-transition mode), distinguishable
# only by the "Authentication" column reporting SAE instead of PSK. This
# table normalizes what we've actually seen reported in the wild.
_KNOWN_ENCRYPTIONS = ("WPA3", "WPA2", "WPA", "WEP")


def _normalize_encryption(privacy: str, auth: str = "") -> str:
    """Map airodump-ng's raw Privacy/Authentication columns to one of
    OPN/WEP/WPA/WPA2/WPA3. SAE authentication means WPA3 even if the
    Privacy column still says WPA2 (common during a WPA3 transition)."""
    privacy_u = (privacy or "").strip().upper()
    auth_u = (auth or "").strip().upper()

    if "SAE" in auth_u:
        return "WPA3"
    for known in _KNOWN_ENCRYPTIONS:
        if known in privacy_u:
            return known
    if not privacy_u or "OPN" in privacy_u:
        return "OPN"
    return privacy_u  # unrecognized string — pass through rather than guess


def parse_airodump_csv(content: str) -> list[APRecord]:
    """Pure parser, unit-testable with a string fixture instead of real hardware.

    airodump-ng's CSV has two sections separated by a blank line: an AP table
    and a client table. We parse the AP table for the record fields, then
    scan the client table to fill in each AP's client count.
    """
    if _CLIENT_HEADER_MARKER in content:
        ap_section, client_section = content.split(_CLIENT_HEADER_MARKER, 1)
        client_section = _CLIENT_HEADER_MARKER + client_section
    else:
        ap_section, client_section = content, ""

    aps: dict[str, APRecord] = {}
    rows = list(csv.reader(StringIO(ap_section.strip())))
    for row in rows[1:]:  # rows[0] is the AP header line
        row = [c.strip() for c in row]
        if len(row) < 14 or not row[0]:
            continue
        bssid = row[0].upper()
        channel = row[3]
        privacy = row[5]
        auth = row[7] if len(row) > 7 else ""
        encryption = _normalize_encryption(privacy, auth)
        try:
            signal = int(row[8])
        except (ValueError, IndexError):
            signal = None
        essid = row[13] or "(hidden)"
        aps[bssid] = APRecord(
            bssid=bssid, essid=essid, channel=channel,
            encryption=encryption, signal=signal, wps=False, clients=0,
        )

    client_counts: dict[str, int] = {}
    if client_section:
        client_rows = list(csv.reader(StringIO(client_section.strip())))
        for row in client_rows[1:]:
            row = [c.strip() for c in row]
            if len(row) < 6:
                continue
            client_bssid = row[5].upper()
            if client_bssid and client_bssid != "(NOT ASSOCIATED)":
                client_counts[client_bssid] = client_counts.get(client_bssid, 0) + 1

    for bssid, count in client_counts.items():
        if bssid in aps:
            ap = aps[bssid]
            aps[bssid] = APRecord(
                bssid=ap.bssid, essid=ap.essid, channel=ap.channel,
                encryption=ap.encryption, signal=ap.signal, wps=ap.wps,
                clients=count,
            )

    return list(aps.values())


class ScannerThread(QThread):
    aps_updated = pyqtSignal(list)   # list[APRecord]
    error = pyqtSignal(str)

    def __init__(self, mon_iface: str, csv_prefix: str = "/tmp/scopesentry_scan",
                 poll_seconds: float = 1.5):
        super().__init__()
        self.mon_iface = mon_iface
        self.csv_prefix = csv_prefix
        self.poll_seconds = poll_seconds
        self._running = True
        self._proc: subprocess.Popen | None = None

    def run(self):
        cmd = ["airodump-ng", self.mon_iface, "--write", self.csv_prefix,
               "--output-format", "csv"]
        try:
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            self.error.emit("airodump-ng not found — install aircrack-ng")
            return

        csv_path = f"{self.csv_prefix}-01.csv"
        while self._running:
            time.sleep(self.poll_seconds)
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    self.aps_updated.emit(parse_airodump_csv(content))
                except OSError as exc:
                    self.error.emit(str(exc))

    def stop(self):
        self._running = False
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()