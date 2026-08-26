"""
core/stats.py
─────────────
Statistics — accumulates real-time counters and produces a rich
end-of-session summary table.

Tracks:
  • Total packets and bytes
  • Per-protocol breakdown (TCP/UDP/ICMP/ARP/DNS/Other)
  • Top-10 source IPs  (talkers)
  • Top-10 destination IPs
  • Top-10 ports
  • Packets/second and KB/s throughput
  • Session duration
"""

import time
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich         import box

from scapy.all import IP, IPv6, TCP, UDP, ICMP, ARP, DNS


class Statistics:
    """Thread-safe packet statistics accumulator."""

    def __init__(self):
        self.console       = Console()
        self._start_time   = time.time()
        self._start_dt     = datetime.now()

        # Totals
        self.total_packets = 0
        self.total_bytes   = 0

        # Per-protocol packet counts
        self.proto_counts  = Counter()

        # Per-protocol byte counts
        self.proto_bytes   = Counter()

        # Top talkers / listeners
        self.src_ips       = Counter()
        self.dst_ips       = Counter()

        # Top ports
        self.src_ports     = Counter()
        self.dst_ports     = Counter()

        # Flag counts (TCP)
        self.tcp_flags     = Counter()

        # Packet sizes
        self.size_bins     = Counter()   # <64, 64-127, 128-511, 512-1023, 1024+

        # Per-second buckets for throughput graph
        self._sec_packets  = defaultdict(int)
        self._sec_bytes    = defaultdict(int)

    # ── Update ────────────────────────────────────────────────

    def update(self, pkt, ts: str):
        """Called once per accepted packet."""
        size = len(pkt)
        self.total_packets += 1
        self.total_bytes   += size

        # Size bin
        if size < 64:
            self.size_bins["<64 B"] += 1
        elif size < 128:
            self.size_bins["64-127 B"] += 1
        elif size < 512:
            self.size_bins["128-511 B"] += 1
        elif size < 1024:
            self.size_bins["512-1023 B"] += 1
        else:
            self.size_bins["1024+ B"] += 1

        # Per-second bucket
        sec = int(time.time() - self._start_time)
        self._sec_packets[sec] += 1
        self._sec_bytes[sec]   += size

        # IP layer
        ip_layer = None
        if IP in pkt:
            ip_layer = pkt[IP]
            self.src_ips[ip_layer.src] += 1
            self.dst_ips[ip_layer.dst] += 1
        elif IPv6 in pkt:
            ip_layer = pkt[IPv6]
            self.src_ips[ip_layer.src] += 1
            self.dst_ips[ip_layer.dst] += 1

        # Protocol layer
        if ARP in pkt:
            self.proto_counts["ARP"] += 1
            self.proto_bytes["ARP"]  += size
        elif DNS in pkt:
            self.proto_counts["DNS"] += 1
            self.proto_bytes["DNS"]  += size
            if UDP in pkt:
                self._update_ports(pkt[UDP])
        elif TCP in pkt:
            tcp = pkt[TCP]
            self.proto_counts["TCP"] += 1
            self.proto_bytes["TCP"]  += size
            self._update_ports(tcp)
            # TCP flags
            for flag in ["SYN", "ACK", "FIN", "RST", "PSH", "URG"]:
                if flag[0] in str(tcp.flags):
                    self.tcp_flags[flag] += 1
        elif UDP in pkt:
            self.proto_counts["UDP"] += 1
            self.proto_bytes["UDP"]  += size
            self._update_ports(pkt[UDP])
        elif ICMP in pkt:
            self.proto_counts["ICMP"] += 1
            self.proto_bytes["ICMP"]  += size
        elif ip_layer:
            self.proto_counts["Other"] += 1
            self.proto_bytes["Other"]  += size

    def _update_ports(self, transport):
        self.src_ports[transport.sport] += 1
        self.dst_ports[transport.dport] += 1

    # ── Summary printer ───────────────────────────────────────

    def print_summary(self):
        elapsed   = time.time() - self._start_time
        duration  = str(timedelta(seconds=int(elapsed)))
        pps       = self.total_packets / elapsed if elapsed > 0 else 0
        kbps      = (self.total_bytes / 1024) / elapsed if elapsed > 0 else 0

        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]Session Duration :[/bold cyan]  {duration}\n"
            f"[bold cyan]Total Packets    :[/bold cyan]  [bold white]{self.total_packets:,}[/bold white]\n"
            f"[bold cyan]Total Bytes      :[/bold cyan]  [bold white]{self.total_bytes:,} B  "
            f"({self.total_bytes / 1024:.1f} KB)[/bold white]\n"
            f"[bold cyan]Avg Throughput   :[/bold cyan]  {pps:.1f} pkt/s  |  {kbps:.1f} KB/s",
            title="[bold yellow]── Session Summary ──[/bold yellow]",
            border_style="yellow"
        ))

        # Protocol breakdown table
        if self.proto_counts:
            t = Table(title="Protocol Breakdown", box=box.SIMPLE_HEAVY,
                      border_style="cyan", show_lines=False)
            t.add_column("Protocol", style="bold cyan",  justify="left")
            t.add_column("Packets",  style="white",      justify="right")
            t.add_column("Bytes",    style="dim white",  justify="right")
            t.add_column("Share",    style="green",      justify="right")

            for proto, count in self.proto_counts.most_common():
                pct  = (count / self.total_packets * 100) if self.total_packets else 0
                bar  = "█" * int(pct / 5)
                byt  = self.proto_bytes[proto]
                t.add_row(proto, f"{count:,}", f"{byt:,} B", f"{bar} {pct:.1f}%")
            self.console.print(t)

        # Top source IPs
        if self.src_ips:
            self._print_top_table("Top Source IPs",      self.src_ips.most_common(10),
                                  ("IP Address", "Packets"))

        # Top destination IPs
        if self.dst_ips:
            self._print_top_table("Top Destination IPs", self.dst_ips.most_common(10),
                                  ("IP Address", "Packets"))

        # Top destination ports
        if self.dst_ports:
            from core.display import PORT_LABELS
            top_ports = [(f"{p} ({PORT_LABELS.get(p, '?')})", c)
                         for p, c in self.dst_ports.most_common(10)]
            self._print_top_table("Top Destination Ports", top_ports,
                                  ("Port", "Packets"))

        # TCP flags
        if self.tcp_flags:
            self._print_top_table("TCP Flag Counts", self.tcp_flags.most_common(),
                                  ("Flag", "Count"))

        # Packet size distribution
        if self.size_bins:
            self._print_top_table("Packet Size Distribution", self.size_bins.most_common(),
                                  ("Size Range", "Count"))

        # ASCII throughput sparkline
        self._print_sparkline()

    def print_session_summary(self):
        """Called when --stats flag is used (no live session)."""
        self.console.print("[dim]No previous session data in memory.[/dim]")
        self.console.print("[dim]Run a capture session first, then use --stats.[/dim]")

    def _print_top_table(self, title, rows, col_names):
        t = Table(title=title, box=box.SIMPLE, border_style="dim", show_lines=False)
        t.add_column(col_names[0], style="bold white", min_width=24)
        t.add_column(col_names[1], style="cyan",       justify="right")
        for label, count in rows:
            t.add_row(str(label), f"{count:,}")
        self.console.print(t)

    def _print_sparkline(self):
        """ASCII bar chart of packets per second."""
        if not self._sec_packets:
            return
        bars  = "▁▂▃▄▅▆▇█"
        vals  = [self._sec_packets[s] for s in sorted(self._sec_packets)]
        mx    = max(vals) if vals else 1
        spark = "".join(bars[min(int(v / mx * (len(bars) - 1)), len(bars) - 1)] for v in vals)

        self.console.print(
            Panel(
                f"[cyan]{spark}[/cyan]\n"
                f"[dim]0s {'─' * max(0, len(spark) - 8)} {len(vals)}s[/dim]\n"
                f"[dim]Peak: {mx} pkt/s[/dim]",
                title="[dim]Packets / Second[/dim]",
                border_style="dim"
            )
        )
