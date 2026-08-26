"""
core/export.py
──────────────
Exporter — writes captured packets to two output formats:

  1. .pcap  — binary libpcap format; openable in Wireshark, tcpdump, etc.
  2. .json  — structured text; each packet is a JSON object with all
              parsed layer fields, making it easy to analyze with Python,
              jq, or import into Elasticsearch/Splunk.

Both files are written incrementally (one packet at a time) so data
is not lost if the program is killed mid-capture.
"""

import json
import os
from datetime import datetime
from pathlib  import Path

from scapy.all import (
    PcapWriter, IP, IPv6, TCP, UDP, ICMP, ARP, DNS, Raw, Ether
)


class Exporter:
    """
    Writes captured packets to .pcap and .json files.

    Parameters
    ----------
    base_name : str
        Filename base (without extension).
        Output files will be  <base_name>.pcap  and  <base_name>.json
        placed in the current directory (or Desktop if the path is bare).
    """

    def __init__(self, base_name: str):
        # Resolve output path
        if os.sep not in base_name and "/" not in base_name:
            out_dir = Path.home() / "Desktop"
        else:
            out_dir = Path(base_name).parent
            base_name = Path(base_name).name

        out_dir.mkdir(parents=True, exist_ok=True)
        self.pcap_path = str(out_dir / f"{base_name}.pcap")
        self.json_path = str(out_dir / f"{base_name}.json")

        # Open pcap writer (append=False — new file each run)
        self._pcap_writer = PcapWriter(self.pcap_path, append=False, sync=True)

        # Open JSON file
        self._json_file   = open(self.json_path, "w", encoding="utf-8")
        self._json_file.write("[\n")    # start JSON array
        self._first       = True        # for comma management
        self._count       = 0

    # ── Write one packet ──────────────────────────────────────

    def write_packet(self, pkt, ts: str):
        """Persist one packet to both output files."""
        self._write_pcap(pkt)
        self._write_json(pkt, ts)
        self._count += 1

    def finalise(self):
        """Call after capture ends to close files properly."""
        # Close pcap
        try:
            self._pcap_writer.close()
        except Exception:
            pass

        # Close JSON array
        try:
            self._json_file.write("\n]\n")
            self._json_file.close()
        except Exception:
            pass

    # ── Internal: pcap ───────────────────────────────────────

    def _write_pcap(self, pkt):
        """Append one packet to the .pcap file."""
        try:
            self._pcap_writer.write(pkt)
        except Exception:
            pass

    # ── Internal: JSON ───────────────────────────────────────

    def _write_json(self, pkt, ts: str):
        """Serialize one packet to a JSON object and append to file."""
        try:
            record = self._packet_to_dict(pkt, ts)
            comma  = "" if self._first else ","
            self._json_file.write(f"{comma}\n{json.dumps(record, indent=2)}")
            self._json_file.flush()
            self._first = False
        except Exception:
            pass

    @staticmethod
    def _packet_to_dict(pkt, ts: str) -> dict:
        """
        Convert a Scapy packet into a plain Python dict suitable for JSON.

        Each protocol layer gets its own nested key.
        """
        record = {
            "timestamp": ts,
            "length": len(pkt),
            "layers": [],
        }

        # ── Ethernet layer ────────────────────────────────────
        if Ether in pkt:
            eth = pkt[Ether]
            record["ethernet"] = {
                "src": eth.src,
                "dst": eth.dst,
                "type": hex(eth.type),
            }
            record["layers"].append("Ethernet")

        # ── ARP ───────────────────────────────────────────────
        if ARP in pkt:
            arp = pkt[ARP]
            record["arp"] = {
                "op":    "request" if arp.op == 1 else "reply",
                "src_ip":  arp.psrc,
                "dst_ip":  arp.pdst,
                "src_mac": arp.hwsrc,
                "dst_mac": arp.hwdst,
            }
            record["layers"].append("ARP")
            return record

        # ── IP layer ──────────────────────────────────────────
        if IP in pkt:
            ip = pkt[IP]
            record["ip"] = {
                "version": ip.version,
                "src":     ip.src,
                "dst":     ip.dst,
                "ttl":     ip.ttl,
                "proto":   ip.proto,
                "id":      ip.id,
                "flags":   str(ip.flags),
                "tos":     ip.tos,
                "len":     ip.len,
                "chksum":  hex(ip.chksum),
            }
            record["layers"].append("IP")

        elif IPv6 in pkt:
            ip6 = pkt[IPv6]
            record["ipv6"] = {
                "src":      ip6.src,
                "dst":      ip6.dst,
                "hop_limit": ip6.hlim,
                "next_hdr": ip6.nh,
            }
            record["layers"].append("IPv6")

        # ── TCP layer ─────────────────────────────────────────
        if TCP in pkt:
            tcp = pkt[TCP]
            record["tcp"] = {
                "sport":   tcp.sport,
                "dport":   tcp.dport,
                "seq":     tcp.seq,
                "ack":     tcp.ack,
                "flags":   str(tcp.flags),
                "window":  tcp.window,
                "chksum":  hex(tcp.chksum),
            }
            record["layers"].append("TCP")

        # ── UDP layer ─────────────────────────────────────────
        elif UDP in pkt:
            udp = pkt[UDP]
            record["udp"] = {
                "sport":  udp.sport,
                "dport":  udp.dport,
                "len":    udp.len,
                "chksum": hex(udp.chksum),
            }
            record["layers"].append("UDP")

        # ── ICMP layer ────────────────────────────────────────
        elif ICMP in pkt:
            icmp = pkt[ICMP]
            type_map = {0: "echo-reply", 3: "dest-unreachable",
                        8: "echo-request", 11: "time-exceeded"}
            record["icmp"] = {
                "type": type_map.get(icmp.type, icmp.type),
                "code": icmp.code,
                "id":   icmp.id,
                "seq":  icmp.seq,
            }
            record["layers"].append("ICMP")

        # ── DNS layer ─────────────────────────────────────────
        if DNS in pkt:
            dns = pkt[DNS]
            dns_rec = {
                "id":  dns.id,
                "qr":  "response" if dns.qr else "query",
                "questions": [],
                "answers":   [],
            }
            # Questions
            qd = dns.qd
            while qd and hasattr(qd, "qname"):
                dns_rec["questions"].append({
                    "qname":  qd.qname.decode(errors="replace"),
                    "qtype":  qd.qtype,
                })
                qd = qd.payload if hasattr(qd, "payload") else None

            # Answers
            an = dns.an
            while an and hasattr(an, "rrname"):
                try:
                    rdata = str(an.rdata) if hasattr(an, "rdata") else "?"
                except Exception:
                    rdata = "?"
                dns_rec["answers"].append({
                    "rrname": an.rrname.decode(errors="replace"),
                    "rdata":  rdata,
                    "ttl":    getattr(an, "ttl", None),
                })
                an = an.payload if hasattr(an, "payload") else None

            record["dns"] = dns_rec
            record["layers"].append("DNS")

        # ── Raw payload ───────────────────────────────────────
        if Raw in pkt:
            raw = pkt[Raw].load
            record["raw"] = {
                "length":  len(raw),
                "hex":     raw[:64].hex(),
                "ascii":   "".join(chr(b) if 32 <= b < 127 else "."
                                   for b in raw[:64]),
            }
            record["layers"].append("Raw")

        return record
