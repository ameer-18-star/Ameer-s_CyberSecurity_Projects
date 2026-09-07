"""Read-only hardening checklist for YOUR own baseline APs.

This never triggers an attack, even though it's flagging the same
weaknesses (WPS, open/WEP encryption) that WPS Pixie Dust and basic packet
capture exploit — the difference is this only reports, on networks you've
explicitly listed as your own, so you can go fix them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.models import APRecord, Finding


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_ENCRYPTION_SEVERITY = {
    "OPN": Severity.HIGH,
    "WEP": Severity.HIGH,
    "WPA": Severity.MEDIUM,
}
_NO_FINDING_ENCRYPTIONS = {"WPA2", "WPA3"}


@dataclass(frozen=True)
class HardeningFinding:
    essid: str
    issue: str
    severity: Severity
    recommendation: str = ""
    code: str = ""

    def to_finding(self) -> Finding:
        """Bridge into the general persisted-Finding shape core/db.py expects."""
        severity_map = {Severity.HIGH: "critical", Severity.MEDIUM: "warning", Severity.LOW: "info"}
        return Finding(
            source="hardening",
            finding_type=self.code or "hardening_finding",
            essid=self.essid,
            severity=severity_map[self.severity],
            details={"issue": self.issue, "recommendation": self.recommendation},
        )


def audit(observed_aps: list[APRecord], baseline_essids: set[str]) -> list[HardeningFinding]:
    findings: list[HardeningFinding] = []
    for ap in observed_aps:
        if ap.essid not in baseline_essids:
            continue

        enc = (ap.encryption or "").strip().upper()
        if enc in _NO_FINDING_ENCRYPTIONS:
            pass
        elif enc in _ENCRYPTION_SEVERITY:
            findings.append(HardeningFinding(
                essid=ap.essid,
                issue=f"Weak encryption: {enc}",
                severity=_ENCRYPTION_SEVERITY[enc],
                recommendation="Move to WPA2-AES or WPA3-SAE",
                code="weak_encryption",
            ))
        else:
            findings.append(HardeningFinding(
                essid=ap.essid,
                issue=f"Unrecognized encryption: {enc or '(none)'}",
                severity=Severity.LOW,
                recommendation="Verify the encryption type manually",
                code="unrecognized_encryption",
            ))

        if ap.wps:
            findings.append(HardeningFinding(
                essid=ap.essid,
                issue="WPS enabled",
                severity=Severity.HIGH,
                recommendation="Disable WPS — vulnerable to Pixie Dust / PIN attacks",
                code="wps_enabled",
            ))

    return findings