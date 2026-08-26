"""
core/filters.py
───────────────
FilterEngine — converts user-friendly options (protocol name, port,
src/dst IP) into:
  1. A BPF (Berkeley Packet Filter) string passed to Scapy's sniff()
     — kernel-level, fast, eliminates packets before Python even sees them.
  2. A Python-level match() check for conditions BPF can't express
     (e.g. filtering by src OR dst IP simultaneously).
"""

from scapy.all import IP, IPv6, TCP, UDP, ICMP, ARP, DNS, Raw


# Map friendly protocol names → BPF expressions
PROTO_BPF = {
    "all":   "",
    "tcp":   "tcp",
    "udp":   "udp",
    "icmp":  "icmp",
    "arp":   "arp",
    "dns":   "udp port 53",
    "http":  "tcp port 80",
    "https": "tcp port 443",
    "ftp":   "tcp port 21",
    "ssh":   "tcp port 22",
}

# Map friendly protocol names → well-known ports (used in display)
PROTO_PORTS = {
    "dns":   53,
    "http":  80,
    "https": 443,
    "ftp":   21,
    "ssh":   22,
}


class FilterEngine:
    """
    Converts CLI filter options into BPF + Python-level checks.

    Parameters
    ----------
    protocol : str
        One of the keys in PROTO_BPF.
    port     : int | None
        Additional port filter (applied on top of protocol filter).
    src_ip   : str | None
        Only show packets from this source IP.
    dst_ip   : str | None
        Only show packets to this destination IP.
    """

    def __init__(self, protocol="all", port=None, src_ip=None, dst_ip=None):
        self.protocol = protocol.lower() if protocol else "all"
        self.port     = port
        self.src_ip   = src_ip
        self.dst_ip   = dst_ip

    def build_bpf(self) -> str:
        """
        Build the BPF filter string for Scapy's sniff().

        BPF runs in the kernel and is very efficient — it drops
        unwanted packets before Python ever sees them.
        """
        parts = []

        # Protocol / well-known-port clause
        base = PROTO_BPF.get(self.protocol, "")
        if base:
            parts.append(base)

        # Custom port clause (only add if not already implied by protocol)
        if self.port and self.protocol not in PROTO_PORTS:
            parts.append(f"port {self.port}")
        elif self.port and self.protocol in PROTO_PORTS:
            # Override the protocol's default port
            parts.append(f"port {self.port}")

        # IP address clauses
        if self.src_ip:
            parts.append(f"src host {self.src_ip}")
        if self.dst_ip:
            parts.append(f"dst host {self.dst_ip}")

        bpf = " and ".join(parts)
        return bpf

    def match(self, pkt) -> bool:
        """
        Python-level secondary check.

        Returns True if the packet should be processed/displayed.
        This catches any edge cases the BPF string doesn't cover.
        """
        # IP address matching (redundant with BPF, but defensive)
        if self.src_ip or self.dst_ip:
            if IP in pkt:
                if self.src_ip and pkt[IP].src != self.src_ip:
                    return False
                if self.dst_ip and pkt[IP].dst != self.dst_ip:
                    return False
            elif IPv6 in pkt:
                if self.src_ip and pkt[IPv6].src != self.src_ip:
                    return False
                if self.dst_ip and pkt[IPv6].dst != self.dst_ip:
                    return False
            else:
                return False    # no IP layer at all

        return True

    def summary(self) -> str:
        """Human-readable description of active filters."""
        parts = [f"protocol={self.protocol}"]
        if self.port:
            parts.append(f"port={self.port}")
        if self.src_ip:
            parts.append(f"src={self.src_ip}")
        if self.dst_ip:
            parts.append(f"dst={self.dst_ip}")
        return "  |  ".join(parts)
