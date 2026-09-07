"""Interface management: enumerate wireless interfaces and toggle monitor mode.

Monitor mode is needed for passive listening (the defense monitors, and the
recon scan) just as much as it would be for an attack — it's a prerequisite
for any 802.11 frame capture, offensive or not. This module only enumerates
interfaces and starts/stops monitor mode. It never deauths, injects, or
invokes an attack/cracking tool.
"""

from __future__ import annotations

import re
import subprocess

from core.command_runner import CommandRunner

_IFACE_RE = re.compile(r"Interface\s+(\S+)")


def parse_iw_dev(output: str) -> list[str]:
    """Pure parser for `iw dev` output -> interface names. Unit-testable
    without touching real hardware."""
    return _IFACE_RE.findall(output)


class InterfaceManager:
    @staticmethod
    def list_interfaces() -> list[str]:
        try:
            result = subprocess.run(
                ["iw", "dev"], capture_output=True, text=True, check=False
            )
        except FileNotFoundError:
            return []
        return parse_iw_dev(result.stdout)

    @staticmethod
    def start_monitor_mode(iface: str) -> CommandRunner:
        return CommandRunner(["airmon-ng", "start", iface])

    @staticmethod
    def stop_monitor_mode(mon_iface: str) -> CommandRunner:
        return CommandRunner(["airmon-ng", "stop", mon_iface])