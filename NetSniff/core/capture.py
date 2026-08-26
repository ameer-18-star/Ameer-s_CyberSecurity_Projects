"""
core/capture.py
───────────────
PacketCapture — wraps Scapy's sniff() and routes every packet
through the filter engine, display engine, and exporter.
"""

import threading
from datetime import datetime

from scapy.all import sniff, AsyncSniffer


class PacketCapture:
    """
    Manages the packet capture lifecycle.

    Parameters
    ----------
    interface : str
        Network interface to listen on (e.g. 'eth0', 'wlan0').
    filters   : FilterEngine
        Decides whether a given packet should be displayed/saved.
    stats     : Statistics
        Accumulates counters and per-protocol breakdowns.
    display   : Display
        Prints formatted packet summaries to the terminal.
    exporter  : Exporter | None
        If provided, writes .pcap and .json output files.
    count     : int
        Maximum packets to capture (0 = unlimited).
    """

    def __init__(self, interface, filters, stats, display, exporter, count=0):
        self.interface = interface
        self.filters   = filters
        self.stats     = stats
        self.display   = display
        self.exporter  = exporter
        self.count     = count          # 0 = unlimited
        self._sniffer  = None
        self._stopped  = threading.Event()
        self._captured = 0              # packets seen after filter

    # ── Public API ────────────────────────────────────────────

    def start(self):
        """Begin sniffing (blocks until count reached or stop() called)."""
        bpf = self.filters.build_bpf()          # e.g. "tcp port 80"

        try:
            sniff(
                iface=self.interface,
                filter=bpf,
                prn=self._process_packet,
                count=self.count,               # 0 = sniff forever
                store=False,                    # don't buffer in RAM
                stop_filter=lambda p: self._stopped.is_set(),
            )
        except PermissionError:
            self.display.error("Permission denied. Run with sudo / as Administrator.")
        except OSError as e:
            self.display.error(f"Interface error: {e}")

    def stop(self):
        """Signal the sniff loop to exit on next packet."""
        self._stopped.set()

    # ── Internal callback ─────────────────────────────────────

    def _process_packet(self, pkt):
        """Called by Scapy for every packet that passes the BPF filter."""

        # Secondary (Python-level) filter for things BPF can't express
        if not self.filters.match(pkt):
            return

        self._captured += 1
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Update statistics
        self.stats.update(pkt, ts)

        # Print to terminal
        self.display.print_packet(pkt, ts, self._captured)

        # Write to files
        if self.exporter:
            self.exporter.write_packet(pkt, ts)

        # Auto-stop if count reached (belt-and-suspenders)
        if self.count and self._captured >= self.count:
            self._stopped.set()
