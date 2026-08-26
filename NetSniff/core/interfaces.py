"""
core/interfaces.py
──────────────────
InterfaceManager — discovers, validates, and displays available
network interfaces using Scapy's built-in interface enumeration.

Works on Windows, Linux, and macOS.
"""

import socket
from rich.console import Console
from rich.table   import Table
from rich         import box

from scapy.all import conf, get_if_list, get_if_addr, get_if_hwaddr


class InterfaceManager:
    """Wraps Scapy's interface discovery with a rich display layer."""

    def __init__(self):
        self.console = Console()

    # ── Public API ────────────────────────────────────────────

    def list_interfaces(self) -> dict:
        """
        Return a dict of  { iface_name: { ip, mac, is_up } }.
        Interfaces with no IP are still included (useful for monitoring mode).
        """
        interfaces = {}
        for iface in get_if_list():
            try:
                ip  = get_if_addr(iface)
            except Exception:
                ip  = "0.0.0.0"
            try:
                mac = get_if_hwaddr(iface)
            except Exception:
                mac = "??:??:??:??:??:??"

            interfaces[iface] = {
                "ip":  ip  if ip  != "0.0.0.0" else "—",
                "mac": mac,
                "is_up": ip != "0.0.0.0",
            }
        return interfaces

    def get_default_interface(self) -> str:
        """Return Scapy's best-guess default interface."""
        try:
            return conf.iface
        except Exception:
            return "eth0"

    def validate(self, iface: str) -> bool:
        """Return True if the interface exists on this system."""
        return iface in get_if_list()

    def print_interfaces(self):
        """Pretty-print all available interfaces in a Rich table."""
        interfaces = self.list_interfaces()
        default    = self.get_default_interface()

        t = Table(
            title="[bold cyan]Available Network Interfaces[/bold cyan]",
            box=box.SIMPLE_HEAVY, border_style="cyan",
            show_lines=False
        )
        t.add_column("#",          style="dim",          justify="right", width=4)
        t.add_column("Interface",  style="bold white",   justify="left",  min_width=14)
        t.add_column("IP Address", style="cyan",         justify="left",  min_width=16)
        t.add_column("MAC Address",style="dim white",    justify="left",  min_width=20)
        t.add_column("Status",     style="green",        justify="center", width=10)
        t.add_column("Default",    style="yellow",       justify="center", width=9)

        for idx, (name, info) in enumerate(interfaces.items(), 1):
            status  = "[green]UP[/green]"   if info["is_up"] else "[dim]DOWN[/dim]"
            default_mark = "[bold yellow]★[/bold yellow]" if name == default else ""
            t.add_row(
                str(idx),
                name,
                info["ip"],
                info["mac"],
                status,
                default_mark,
            )

        self.console.print(t)
        self.console.print(
            f"\n[dim]Default interface (★): [bold]{default}[/bold][/dim]\n"
            f"[dim]Use [bold]-i <name>[/bold] to specify an interface.[/dim]\n"
        )
