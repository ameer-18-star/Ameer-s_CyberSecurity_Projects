"""Engagement manifest: the authorized-scope-and-window record for a sanctioned
assessment.

This module has no attack capability of its own — it's a standalone
authorization-tracking library. Its job is to answer one question reliably:
"is this BSSID, right now, inside what was actually authorized?" Anything
that builds or runs an active command is expected to call `authorize()`
before doing so and refuse to proceed if it returns False.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_BSSID_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


class InvalidManifest(ValueError):
    """Raised when a manifest file is missing required fields or is internally inconsistent."""


@dataclass(frozen=True)
class EngagementManifest:
    engagement_id: str
    client: str
    tester: str
    authorized_by: str
    window_start: datetime
    window_end: datetime
    authorized_bssids: frozenset[str]

    # ---- loading & validation -------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "EngagementManifest":
        required = ("engagement_id", "client", "tester", "authorized_by",
                    "window_start", "window_end", "authorized_targets")
        missing = [k for k in required if k not in data]
        if missing:
            raise InvalidManifest(f"manifest missing required field(s): {', '.join(missing)}")

        targets = data["authorized_targets"]
        if not isinstance(targets, list) or len(targets) == 0:
            raise InvalidManifest("authorized_targets must be a non-empty list")

        bssids = set()
        for t in targets:
            bssid = t.get("bssid", "") if isinstance(t, dict) else ""
            if not _BSSID_RE.match(bssid):
                raise InvalidManifest(f"invalid BSSID in authorized_targets: {bssid!r}")
            bssids.add(bssid.upper())

        try:
            start = datetime.fromisoformat(data["window_start"])
            end = datetime.fromisoformat(data["window_end"])
        except (TypeError, ValueError) as exc:
            raise InvalidManifest(f"window_start/window_end must be ISO-8601: {exc}") from exc

        if end <= start:
            raise InvalidManifest("window_end must be after window_start")

        return cls(
            engagement_id=str(data["engagement_id"]),
            client=str(data["client"]),
            tester=str(data["tester"]),
            authorized_by=str(data["authorized_by"]),
            window_start=start,
            window_end=end,
            authorized_bssids=frozenset(bssids),
        )

    @classmethod
    def load(cls, path: str | Path) -> "EngagementManifest":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    # ---- the gate ---------------------------------------------------------

    def is_in_scope(self, bssid: str) -> bool:
        return bssid.strip().upper() in self.authorized_bssids

    def is_within_window(self, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        return self.window_start <= now <= self.window_end

    def authorize(self, bssid: str, now: datetime | None = None) -> bool:
        """The single call every active/offensive code path must pass before
        doing anything. Both conditions must hold; there is no override."""
        return self.is_in_scope(bssid) and self.is_within_window(now)

    def reason_if_blocked(self, bssid: str, now: datetime | None = None) -> str | None:
        """Human-readable reason for a UI/log message, or None if authorized."""
        if not self.is_in_scope(bssid):
            return f"{bssid} is not in the authorized_targets list for {self.engagement_id}"
        if not self.is_within_window(now):
            return f"current time is outside the engagement window for {self.engagement_id}"
        return None