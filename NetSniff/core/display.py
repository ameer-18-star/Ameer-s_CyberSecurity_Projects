"""
core/display.py
───────────────
Display — formats and prints every captured packet to the terminal
using Rich for colored, structured output.

Handles: Ethernet, ARP, IP, IPv6, TCP, UDP, ICMP, DNS, HTTP, Raw payload.
"""

import textwrap

from rich.console import Console
from rich.table   import Table
from rich.text    import Text
from rich.panel   import Panel
from rich         import box

from scapy.all import (
    Ether, ARP, IP, IPv6, TCP, UDP, ICMP, ICMPv6EchoRequest,
    ICMPv6EchoReply, DNS, DNSQR, DNSRR, Raw
)


# ── Protocol colour palette ───────────────────────────────────
COLOURS = {
    "TCP":   "bold cyan",
    "UDP":   "bold green",
    "ICMP":  "bold yellow",
    "ARP":   "bold magenta",
    "DNS":   "bold blue",
    "HTTP":  "bold orange1",
    "HTTPS": "bold red",
    "OTHER": "dim white",
}

# Well-known port → label
PORT_LABELS = {
    20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "TELNET",
    25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    445: "SMB", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    6379: "Redis", 8080: "HTTP-ALT", 8443: "HTTPS-ALT",
    27017: "MongoDB",
}


def port_label(port: int) -> str:
    return PORT_LABELS.get(port, str(port))


class Display:
    """
    Renders packet summaries to the terminal.

    Parameters
    ----------
    verbose  : bool   Show full payload bytes (hex + ASCII)
    no_color : bool   Disable all Rich colour codes
    """

    def __init__(self, verbose=False, no_color=False):
        self.verbose  = verbose
        self.console  = Console(highlight=False, no_color=no_color)
        self._counter = 0

    # ── Public helpers ────────────────────────────────────────

    def error(self, msg: str):
        self.console.print(f"[bold red][ERROR][/bold red] {msg}")

    def print_capture_header(self, args):
        """Print the capture session summary banner."""
        from datetime import datetime
        bpf_hint = f"Protocol: [bold]{args.filter}[/bold]"
        if args.port:
            bpf_hint += f"  Port: [bold]{args.port}[/bold]"
        if args.src:
            bpf_hint += f"  Src: [bold]{args.src}[/bold]"
        if args.dst:
            bpf_hint += f"  Dst: [bold]{args.dst}[/bold]"

        content = (
            f"[bold green]Interface :[/bold green]  {args.interface}\n"
            f"[bold green]Filter    :[/bold green]  {bpf_hint}\n"
            f"[bold green]Count     :[/bold green]  {'unlimited' if args.count == 0 else args.count}\n"
            f"[bold green]Output    :[/bold green]  {'[dim]none[/dim]' if not args.output else args.output + '.pcap / .json'}\n"
            f"[bold green]Started   :[/bold green]  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}\n\n"
            f"[dim]Press Ctrl+C to stop and view summary.[/dim]"
        )
        self.console.print(Panel(content, title="[bold cyan]NetSniff — Capture Session[/bold cyan]",
                                 border_style="cyan"))

        # Column header
        header = (
            f"{'#':>5}  {'Time':>12}  {'Proto':>6}  "
            f"{'Source':>21}  {'Destination':>21}  {'Info'}"
        )
        self.console.print(f"\n[bold dim]{header}[/bold dim]")
        self.console.print("[dim]" + "─" * 100 + "[/dim]")

    def print_packet(self, pkt, ts: str, num: int):
        """Dispatch to the correct per-protocol formatter."""
        if ARP in pkt:
            self._print_arp(pkt, ts, num)
        elif ICMP in pkt:
            self._print_icmp(pkt, ts, num)
        elif DNS in pkt:
            self._print_dns(pkt, ts, num)
        elif TCP in pkt:
            self._print_tcp(pkt, ts, num)
        elif UDP in pkt:
            self._print_udp(pkt, ts, num)
        elif IP in pkt or IPv6 in pkt:
            self._print_generic_ip(pkt, ts, num)
        else:
            self._print_raw(pkt, ts, num)

    # ── Protocol-specific printers ────────────────────────────

    def _print_tcp(self, pkt, ts, num):
        ip   = pkt[IP] if IP in pkt else pkt[IPv6]
        tcp  = pkt[TCP]
        sport, dport = tcp.sport, tcp.dport

        # Determine label (HTTP / HTTPS / SSH / etc.)
        if dport == 80 or sport == 80:
            proto_tag = "HTTP"
        elif dport == 443 or sport == 443:
            proto_tag = "HTTPS"
        else:
            proto_tag = "TCP"

        flags = self._tcp_flags(tcp.flags)
        src = f"{ip.src}:{port_label(sport)}"
        dst = f"{ip.dst}:{port_label(dport)}"
        info = f"Flags=[{flags}]  Seq={tcp.seq}  Ack={tcp.ack}  Win={tcp.window}"
        size = len(pkt)

        colour = COLOURS.get(proto_tag, COLOURS["TCP"])
        self._print_row(num, ts, proto_tag, src, dst, info, size, colour)

        # HTTP payload preview
        if (dport == 80 or sport == 80) and Raw in pkt:
            self._print_http_preview(pkt[Raw].load)

        if self.verbose and Raw in pkt:
            self._print_payload(pkt[Raw].load)

    def _print_udp(self, pkt, ts, num):
        ip   = pkt[IP] if IP in pkt else pkt[IPv6]
        udp  = pkt[UDP]
        src  = f"{ip.src}:{port_label(udp.sport)}"
        dst  = f"{ip.dst}:{port_label(udp.dport)}"
        info = f"Len={udp.len}  Chksum=0x{udp.chksum:04X}"
        size = len(pkt)

        self._print_row(num, ts, "UDP", src, dst, info, size, COLOURS["UDP"])

        if self.verbose and Raw in pkt:
            self._print_payload(pkt[Raw].load)

    def _print_icmp(self, pkt, ts, num):
        ip   = pkt[IP]
        icmp = pkt[ICMP]
        type_names = {0: "Echo Reply", 3: "Dest Unreachable",
                      8: "Echo Request", 11: "Time Exceeded"}
        type_str = type_names.get(icmp.type, f"Type={icmp.type}")
        src  = ip.src
        dst  = ip.dst
        info = f"{type_str}  Code={icmp.code}  ID={icmp.id}  Seq={icmp.seq}"
        size = len(pkt)

        self._print_row(num, ts, "ICMP", src, dst, info, size, COLOURS["ICMP"])

    def _print_arp(self, pkt, ts, num):
        arp = pkt[ARP]
        op  = "Request" if arp.op == 1 else "Reply"
        src = f"{arp.psrc} ({arp.hwsrc})"
        dst = f"{arp.pdst} ({arp.hwdst})"
        if arp.op == 1:
            info = f"Who has {arp.pdst}? Tell {arp.psrc}"
        else:
            info = f"{arp.psrc} is at {arp.hwsrc}"
        size = len(pkt)

        self._print_row(num, ts, f"ARP/{op}", src, dst, info, size, COLOURS["ARP"])

    def _print_dns(self, pkt, ts, num):
        ip  = pkt[IP] if IP in pkt else pkt[IPv6]
        dns = pkt[DNS]

        if dns.qr == 0:               # Query
            qname = dns.qd.qname.decode(errors="replace") if dns.qd else "?"
            info  = f"Query: {qname}"
        else:                         # Response
            answers = []
            rr = dns.an
            while rr and rr.type != 0:
                try:
                    answers.append(rr.rdata if hasattr(rr, "rdata") else "?")
                except Exception:
                    pass
                rr = rr.payload if hasattr(rr, "payload") else None
            info = f"Response: {', '.join(str(a) for a in answers[:3])}"

        src  = ip.src
        dst  = ip.dst
        size = len(pkt)

        self._print_row(num, ts, "DNS", src, dst, info, size, COLOURS["DNS"])

    def _print_generic_ip(self, pkt, ts, num):
        ip   = pkt[IP] if IP in pkt else pkt[IPv6]
        proto = ip.proto if hasattr(ip, "proto") else "?"
        info  = f"IP proto={proto}  TTL={getattr(ip, 'ttl', '?')}"
        size  = len(pkt)

        self._print_row(num, ts, "IP", ip.src, ip.dst, info, size, COLOURS["OTHER"])

    def _print_raw(self, pkt, ts, num):
        info = f"Non-IP frame  len={len(pkt)}"
        self._print_row(num, ts, "RAW", "—", "—", info, len(pkt), COLOURS["OTHER"])

    # ── Row & payload helpers ─────────────────────────────────

    def _print_row(self, num, ts, proto, src, dst, info, size, colour):
        """Print one 100-char-wide summary line."""
        proto_col = f"[{colour}]{proto:<7}[/{colour}]"
        line = (
            f"[dim]{num:>5}[/dim]  "
            f"[dim]{ts}[/dim]  "
            f"{proto_col}  "
            f"[white]{src:>21}[/white]  "
            f"[white]{dst:>21}[/white]  "
            f"[dim]{info[:50]}[/dim]  "
            f"[dim]{size}B[/dim]"
        )
        self.console.print(line)

    def _print_http_preview(self, payload: bytes):
        """Show the first line of an HTTP request/response."""
        try:
            text = payload.decode("utf-8", errors="replace")
            first_line = text.split("\r\n")[0][:120]
            self.console.print(f"  [bold orange1]HTTP:[/bold orange1] [dim]{first_line}[/dim]")
        except Exception:
            pass

    def _print_payload(self, payload: bytes):
        """Print hex + ASCII dump of raw payload (verbose mode)."""
        self.console.print("  [dim]── Payload ──────────────────────────────[/dim]")
        for i in range(0, min(len(payload), 256), 16):
            chunk = payload[i:i + 16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            asc_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            self.console.print(
                f"  [dim cyan]{i:04X}[/dim cyan]  "
                f"[dim]{hex_part:<48}[/dim]  "
                f"[green]{asc_part}[/green]"
            )
        if len(payload) > 256:
            self.console.print(f"  [dim]... {len(payload) - 256} more bytes[/dim]")
        self.console.print("  [dim]────────────────────────────────────────[/dim]")

    # ── TCP flag decoder ──────────────────────────────────────

    @staticmethod
    def _tcp_flags(flags) -> str:
        """Convert Scapy TCP flags integer to a human-readable string."""
        flag_map = {
            "F": "FIN", "S": "SYN", "R": "RST",
            "P": "PSH", "A": "ACK", "U": "URG",
            "E": "ECE", "C": "CWR",
        }
        result = []
        flags_str = str(flags)
        for char, name in flag_map.items():
            if char in flags_str:
                result.append(name)
        return "|".join(result) if result else "NONE"
