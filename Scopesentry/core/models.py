"""Shared data models.

APRecord is the single representation of an observed access point used
across the project — the scanner populates it, the defense monitors and
GUI consume it. Finding is a general-purpose record for persisting to
core/db.py; the more specific alert/finding types in core/defense/* each
provide a to_finding() bridge so they can be stored the same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class APRecord:
    """A single access point observation from a passive scan."""

    bssid: str
    essid: str
    channel: str
    encryption: str            # OPN / WEP / WPA / WPA2 / WPA3 (as reported by the scan)
    signal: int | None = None  # dBm-ish power reading, may be unavailable
    wps: bool = False
    clients: int = 0

    @property
    def bssid_norm(self) -> str:
        return self.bssid.strip().upper()

    def normalized_bssid(self) -> str:
        """Back-compat alias for bssid_norm."""
        return self.bssid_norm


@dataclass(frozen=True)
class BaselineAP:
    """A known-good AP you own, used by the defense modules as ground truth."""

    essid: str
    bssid: str
    expected_encryption: str
    expected_channel: str


@dataclass
class Finding:
    """General-purpose persisted finding — what core/db.py actually stores.
    Module-specific alert/finding types (RogueAlert, HardeningFinding) each
    expose to_finding() to convert into this shape."""

    source: str          # "rogue_ap" | "hardening" | "deauth_flood"
    finding_type: str
    essid: str
    severity: str = "info"     # info | warning | critical
    details: dict = field(default_factory=dict)