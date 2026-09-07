"""Passive deauthentication/disassociation flood monitor.

This monitor is strictly passive. It runs ``tshark`` in capture mode on a
monitor-mode interface, counts 802.11 deauth (subtype 0x0c) and disassoc
(subtype 0x0a) management frames per BSSID, and raises an alert when the
rate for one of *your own* baseline BSSIDs exceeds a threshold inside a
time window.

It never transmits a frame and never builds an attack command. Its purpose
is to detect someone else attacking networks you operate.

Design notes:
- Only BSSIDs present in ``baseline_bssids`` are counted; everything else
  is ignored, so the monitor is scoped to networks you've declared as yours.
- Counting uses a fixed tumbling window of ``window_seconds``.
- ``tshark`` is launched with line-buffered output (``-l``) so counts
  update promptly.
"""

from __future__ import annotations

import subprocess
import time
from collections import defaultdict

from PyQt6.QtCore import QThread, pyqtSignal

# 802.11 management subtypes: 0x0c = deauthentication, 0x0a = disassociation.
_DEAUTH_DISASSOC_FILTER = (
    "wlan.fc.type_subtype == 0x0c || wlan.fc.type_subtype == 0x0a"
)


class DeauthMonitor(QThread):
    """Emits ``flood_detected(bssid, count)`` when a baseline AP is flooded."""

    flood_detected = pyqtSignal(str, int)   # bssid, frame_count_in_window
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        mon_iface: str,
        baseline_bssids: set[str],
        threshold: int = 15,
        window_seconds: float = 10.0,
        parent=None,
    ):
        super().__init__(parent)
        self.mon_iface = mon_iface
        self.baseline_bssids = {b.strip().upper() for b in baseline_bssids}
        self.threshold = threshold
        self.window_seconds = window_seconds
        self._running = True
        self._proc: subprocess.Popen | None = None

    def _build_cmd(self) -> list[str]:
        return [
            "tshark",
            "-i", self.mon_iface,
            "-l",                       # line-buffered stdout
            "-n",                       # no name resolution
            "-Y", _DEAUTH_DISASSOC_FILTER,
            "-T", "fields",
            "-e", "wlan.bssid",
        ]

    def run(self):
        try:
            self._proc = subprocess.Popen(
                self._build_cmd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except FileNotFoundError:
            self.error.emit("tshark not found — install wireshark-common")
            return
        except OSError as exc:
            self.error.emit(f"failed to start tshark: {exc}")
            return

        self.status.emit(f"monitoring deauth/disassoc on {self.mon_iface}")
        counts: dict[str, int] = defaultdict(int)
        window_start = time.monotonic()

        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            if not self._running:
                break
            bssid = line.strip().upper()
            if bssid and bssid in self.baseline_bssids:
                counts[bssid] += 1

            if time.monotonic() - window_start >= self.window_seconds:
                self._flush(counts)
                counts.clear()
                window_start = time.monotonic()

        # Final flush on shutdown for any partial window.
        self._flush(counts)

    def _flush(self, counts: dict[str, int]):
        for bssid, count in counts.items():
            if count >= self.threshold:
                self.flood_detected.emit(bssid, count)

    def stop(self):
        """Signal the loop to stop and terminate the tshark process."""
        self._running = False
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()