"""Rogue-AP / evil-twin detection against a baseline of your own known-good APs.

Purely analytical: it compares observed ``APRecord`` objects to a baseline
you define for networks you operate, and reports anomalies. It never
transmits and never builds an attack command.

Checks performed for each observed AP whose ESSID matches one of your
baseline SSIDs:

- ``bssid_mismatch``       — your SSID is being advertised from an
                             unexpected BSSID (classic evil twin).
- ``encryption_downgrade`` — your SSID is seen with weaker encryption than
                             expected.
- ``channel_mismatch``     — your SSID is seen on an unexpected channel.

Observed APs whose ESSID is not in the baseline are ignored: this module
only reasons about your own declared networks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.models import APRecord, BaselineAP, Finding


class AlertType(str, Enum):
    BSSID_MISMATCH = "bssid_mismatch"
    ENCRYPTION_DOWNGRADE = "encryption_downgrade"
    CHANNEL_MISMATCH = "channel_mismatch"


_ALERT_SEVERITY = {
    AlertType.BSSID_MISMATCH: "critical",
    AlertType.ENCRYPTION_DOWNGRADE: "warning",
    AlertType.CHANNEL_MISMATCH: "info",
}

# Ordered weakest -> strongest. Anything below the baseline level is a downgrade.
_ENCRYPTION_RANK = {
    "OPN": 0,
    "WEP": 1,
    "WPA": 2,
    "WPA2": 3,
    "WPA3": 4,
}


@dataclass(frozen=True)
class RogueAlert:
    type: AlertType
    essid: str
    detail: dict

    def to_finding(self) -> Finding:
        """Bridge into the general persisted-Finding shape core/db.py expects."""
        return Finding(
            source="rogue_ap",
            finding_type=self.type.value,
            essid=self.essid,
            severity=_ALERT_SEVERITY[self.type],
            details=self.detail,
        )


def _rank(encryption: str) -> int | None:
    return _ENCRYPTION_RANK.get((encryption or "").strip().upper())


class RogueAPMonitor:
    def __init__(self, baseline: list[BaselineAP]):
        # One baseline entry per ESSID. If you run the same SSID on multiple
        # legitimate BSSIDs, model that upstream (e.g. a set of allowed BSSIDs).
        self.baseline: dict[str, BaselineAP] = {b.essid: b for b in baseline}

    def check(self, observed_aps: list[APRecord]) -> list[RogueAlert]:
        alerts: list[RogueAlert] = []
        for ap in observed_aps:
            known = self.baseline.get(ap.essid)
            if known is None:
                continue  # not one of our SSIDs

            if ap.bssid_norm != known.bssid.strip().upper():
                alerts.append(RogueAlert(
                    AlertType.BSSID_MISMATCH, ap.essid,
                    {"seen_bssid": ap.bssid_norm,
                     "expected_bssid": known.bssid.strip().upper()},
                ))

            if self._is_downgrade(ap.encryption, known.expected_encryption):
                alerts.append(RogueAlert(
                    AlertType.ENCRYPTION_DOWNGRADE, ap.essid,
                    {"seen": ap.encryption, "expected": known.expected_encryption},
                ))

            if str(ap.channel) != str(known.expected_channel):
                alerts.append(RogueAlert(
                    AlertType.CHANNEL_MISMATCH, ap.essid,
                    {"seen": ap.channel, "expected": known.expected_channel},
                ))
        return alerts

    @staticmethod
    def _is_downgrade(seen: str, expected: str) -> bool:
        seen_rank = _rank(seen)
        expected_rank = _rank(expected)
        # Unknown encryption string: flag if it doesn't match expected exactly.
        if seen_rank is None or expected_rank is None:
            return (seen or "").strip().upper() != (expected or "").strip().upper()
        return seen_rank < expected_rank