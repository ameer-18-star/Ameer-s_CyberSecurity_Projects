# NetSniff — Educational Network Packet Sniffer
## Detailed Project Report

**Project:** NetSniff v1.0  
**Type:** Command-Line Network Packet Sniffer  
**Language:** Python 3.8+  
**Purpose:** Cybersecurity Education & Internship  
**Total Lines of Code:** 1,361 across 7 modules  
**Date:** July 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Objectives & Feature Checklist](#2-objectives--feature-checklist)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [System Architecture & Data Flow](#5-system-architecture--data-flow)
6. [Component-by-Component Breakdown](#6-component-by-component-breakdown)
   - 6.1 [sniffer.py — Entry Point](#61-snifferpy--entry-point)
   - 6.2 [core/capture.py — Capture Engine](#62-corecapturepy--capture-engine)
   - 6.3 [core/filters.py — Filter Engine](#63-corefilterspy--filter-engine)
   - 6.4 [core/display.py — Display Engine](#64-coredisplaypy--display-engine)
   - 6.5 [core/stats.py — Statistics Engine](#65-corestatspy--statistics-engine)
   - 6.6 [core/export.py — Export Engine](#66-coreexportpy--export-engine)
   - 6.7 [core/interfaces.py — Interface Manager](#67-coreinterfacespy--interface-manager)
7. [Protocol Coverage Deep Dive](#7-protocol-coverage-deep-dive)
8. [BPF — The Two-Layer Filtering System](#8-bpf--the-two-layer-filtering-system)
9. [Output Formats Explained](#9-output-formats-explained)
10. [Session Statistics System](#10-session-statistics-system)
11. [CLI Reference](#11-cli-reference)
12. [How a Packet Sniffer Works — Conceptual Explanation](#12-how-a-packet-sniffer-works--conceptual-explanation)
13. [Ethical & Legal Disclaimer](#13-ethical--legal-disclaimer)
14. [Setup & Usage Guide](#14-setup--usage-guide)
15. [Conclusion](#15-conclusion)

---

## 1. Project Overview

**NetSniff** is a moderate-level, command-line network packet sniffer built entirely in Python for cybersecurity education and internship demonstration purposes. It captures live network traffic flowing through a chosen network interface, decodes it across multiple protocol layers, displays it in a structured and colour-coded terminal view, tracks session-wide statistics, and optionally saves everything to standard file formats.

Unlike simplified single-file packet capture scripts, NetSniff is organized as a proper multi-module Python project with clean separation of concerns — each responsibility (capturing, filtering, displaying, tracking, exporting, interface management) lives in its own dedicated module. This design makes the codebase easy to read, explain, extend, and present.

The tool is powered by two core libraries:

- **Scapy** — the most widely used Python library for packet manipulation and capture, trusted by security professionals and researchers worldwide.
- **Rich** — a modern Python terminal formatting library that provides coloured output, tables, panels, and progress indicators without external dependencies.

Everything runs locally. No data is sent to any external server or service. The tool is designed to be transparent — the Python source is fully readable by anyone reviewing it.

---

## 2. Objectives & Feature Checklist

| # | Feature | Status |
|---|---------|--------|
| 1 | Capture live packets from a real network interface | ✅ |
| 2 | Support multiple protocol filters (TCP, UDP, ICMP, ARP, DNS, HTTP, HTTPS, FTP, SSH) | ✅ |
| 3 | Filter by specific port number | ✅ |
| 4 | Filter by source IP address | ✅ |
| 5 | Filter by destination IP address | ✅ |
| 6 | Decode and display Ethernet layer | ✅ |
| 7 | Decode and display ARP packets | ✅ |
| 8 | Decode and display IP / IPv6 headers | ✅ |
| 9 | Decode and display TCP headers with flag breakdown | ✅ |
| 10 | Decode and display UDP headers | ✅ |
| 11 | Decode and display ICMP type and code | ✅ |
| 12 | Decode and display DNS queries and responses | ✅ |
| 13 | Detect HTTP traffic and show request/response first line | ✅ |
| 14 | Verbose mode — hex + ASCII payload dump | ✅ |
| 15 | Capture a fixed number of packets then stop | ✅ |
| 16 | Save capture to .pcap (Wireshark-compatible) | ✅ |
| 17 | Save capture to structured .json | ✅ |
| 18 | Real-time terminal statistics display | ✅ |
| 19 | End-of-session summary with protocol breakdown table | ✅ |
| 20 | Top-10 source IPs, destination IPs, and ports | ✅ |
| 21 | TCP flag frequency counter | ✅ |
| 22 | Packet size distribution histogram | ✅ |
| 23 | ASCII packets-per-second sparkline graph | ✅ |
| 24 | Average throughput (packets/sec, KB/sec) | ✅ |
| 25 | List all network interfaces with IP, MAC, and status | ✅ |
| 26 | Interactive guided setup menu (no CLI arguments needed) | ✅ |
| 27 | Full CLI argument support via argparse | ✅ |
| 28 | Graceful Ctrl+C shutdown — saves data, prints summary | ✅ |
| 29 | Cross-platform: Linux, macOS, Windows | ✅ |
| 30 | Kernel-level BPF filtering for performance | ✅ |

---

## 3. Technology Stack

| Library / Tool | Version | Role | Why It Was Chosen |
|---|---|---|---|
| **Python** | 3.8+ | Core language | Cross-platform, readable, industry standard for security tools |
| **Scapy** | ≥ 2.5.0 | Packet capture & parsing | The de facto Python packet library; handles BPF, pcap, and all protocol layers |
| **Rich** | ≥ 13.0.0 | Terminal UI | Coloured output, tables, panels, and progress with zero browser dependency |
| **argparse** | stdlib | CLI argument parsing | Built into Python; robust, self-documenting help output |
| **threading** | stdlib | Concurrency | Allows keyboard listener and capture loop to run simultaneously |
| **signal** | stdlib | Graceful shutdown | Intercepts Ctrl+C (SIGINT) and system shutdown (SIGTERM) |
| **collections.Counter** | stdlib | Statistics counters | Efficient frequency counting for IPs, ports, protocols |
| **collections.defaultdict** | stdlib | Per-second buckets | Clean dictionary with default values for throughput tracking |
| **json** | stdlib | JSON serialisation | Standard library JSON writer for output files |
| **pathlib** | stdlib | File paths | Cross-platform path handling (Windows `\` vs Unix `/`) |
| **libpcap / Npcap** | system | Kernel capture driver | OS-level packet capture driver required by Scapy |

### Why Scapy?

Scapy is not just a capture library — it is a full packet manipulation framework. It can:

- **Read** packets from a live interface or a .pcap file.
- **Parse** every layer of a packet into Python objects with named fields.
- **Craft** custom packets from scratch (useful for advanced testing).
- **Write** packets back to a .pcap file in the libpcap binary format.
- **Apply BPF filters** at the kernel level, passing only matching packets to Python.

For this project, Scapy is used for its capture and parsing capabilities.

---

## 4. Project Structure

```
packet_sniffer/
│
├── sniffer.py                 ← Entry point
│                                CLI argument parsing, interactive menu,
│                                component wiring, signal handlers, startup
│
├── requirements.txt           ← pip dependencies (scapy, rich)
│
├── README.md                  ← Quick-start guide and usage examples
│
├── REPORT.md                  ← This document
│
└── core/                      ← Core module package
    │
    ├── __init__.py            ← Package marker (empty)
    │
    ├── capture.py             ← PacketCapture class
    │                            Wraps Scapy sniff(), routes each packet
    │                            through the pipeline
    │
    ├── filters.py             ← FilterEngine class
    │                            Builds BPF strings, performs Python-level
    │                            IP address matching
    │
    ├── display.py             ← Display class
    │                            Protocol-aware Rich terminal formatter;
    │                            separate printer per protocol type
    │
    ├── stats.py               ← Statistics class
    │                            Counters, top-talkers, throughput,
    │                            sparkline, summary printer
    │
    ├── export.py              ← Exporter class
    │                            Incremental .pcap and .json file writers
    │
    └── interfaces.py          ← InterfaceManager class
                                 Interface discovery, validation,
                                 and rich table display
```

### Design Philosophy

The project follows a **pipeline architecture**. Every captured packet flows through a fixed sequence of independent stages:

```
Kernel (BPF) → capture.py → filters.py → stats.py → display.py → export.py
```

Each stage is a separate class in a separate file. None of them knows about the others — they only receive what they need as constructor parameters. This means you can swap out the display engine, add a new export format, or change the statistics logic without touching any other module.

---

## 5. System Architecture & Data Flow

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         USER'S MACHINE                                   │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐     │
│   │                  NETWORK INTERFACES                            │     │
│   │   eth0 (wired)  /  wlan0 (WiFi)  /  lo (loopback)  / ...     │     │
│   └────────────────────────┬───────────────────────────────────────┘     │
│                            │  Raw Ethernet frames flowing through        │
│                            │  the physical/virtual interface             │
│                            ▼                                             │
│   ┌────────────────────────────────────────────────────────────────┐     │
│   │              KERNEL SPACE — BPF Filter                         │     │
│   │                                                                │     │
│   │   libpcap / Npcap applies the BPF expression here.            │     │
│   │   Packets that don't match are DROPPED at the kernel level     │     │
│   │   and never reach Python — very fast, near-zero CPU overhead.  │     │
│   └────────────────────────┬───────────────────────────────────────┘     │
│                            │  Only matching packets pass through         │
│                            ▼                                             │
│   ┌────────────────────────────────────────────────────────────────┐     │
│   │              USER SPACE — Python / Scapy                       │     │
│   │                                                                │     │
│   │   PacketCapture._process_packet(pkt) is called per packet.    │     │
│   │                                                                │     │
│   │   ┌──────────┐    ┌───────────┐    ┌──────────┐              │     │
│   │   │ filters  │───►│  stats   │───►│ display  │              │     │
│   │   │ .match() │    │ .update()│    │.print_   │              │     │
│   │   │          │    │          │    │ packet() │              │     │
│   │   └──────────┘    └───────────┘    └──────────┘              │     │
│   │                                          │                    │     │
│   │                                          ▼                    │     │
│   │                                   ┌──────────┐               │     │
│   │                                   │ exporter │               │     │
│   │                                   │.write_   │               │     │
│   │                                   │ packet() │               │     │
│   │                                   └──────────┘               │     │
│   └──────────────┬─────────────────────────┬──────────────────────┘     │
│                  │                         │                             │
│                  ▼                         ▼                             │
│           Terminal output            Desktop files                       │
│           (Rich coloured)         capture.pcap + capture.json           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Single Packet Journey

The journey of one packet from the moment a key is pressed on a remote server to the moment it appears on the terminal:

```
Remote server sends a TCP ACK to your machine
           │
           ▼
Network card (NIC) receives the Ethernet frame
           │
           ▼
OS kernel's network stack receives the raw frame
           │
           ▼
libpcap intercepts a copy of the frame
(the original continues to its destination normally)
           │
           ▼
BPF filter checks: "Does this match 'tcp port 80'?"
  ├── NO  →  packet silently discarded, never enters Python
  └── YES →  frame passed to Scapy's callback
           │
           ▼
Scapy deserialises the bytes into layered Python objects:
  Ether(src="aa:bb", dst="cc:dd") /
  IP(src="1.2.3.4", dst="192.168.1.5", ttl=52) /
  TCP(sport=80, dport=54321, flags="A", seq=8832, ack=1001) /
  Raw(load=b"HTTP/1.1 200 OK\r\n...")
           │
           ▼
PacketCapture._process_packet(pkt) is called
           │
           ├──► FilterEngine.match(pkt)  →  True  (passes IP check)
           │
           ├──► Statistics.update(pkt)
           │      • total_packets += 1
           │      • total_bytes += 74
           │      • proto_counts["TCP"] += 1
           │      • src_ips["1.2.3.4"] += 1
           │      • dst_ips["192.168.1.5"] += 1
           │      • dst_ports[80] += 1
           │      • tcp_flags["ACK"] += 1
           │      • size_bins["64-127 B"] += 1
           │      • _sec_packets[42] += 1
           │
           ├──► Display.print_packet(pkt)
           │      → _print_tcp() called
           │      → reads IP, TCP layers
           │      → detects port 80 → label "HTTP"
           │      → _tcp_flags("A") → "ACK"
           │      → _print_row() → Rich outputs coloured line
           │      → _print_http_preview() → prints "HTTP/1.1 200 OK"
           │
           └──► Exporter.write_packet(pkt)
                  → _write_pcap()  →  appends raw bytes to .pcap
                  → _write_json()  →  serialises to dict, appends to .json
```

---

## 6. Component-by-Component Breakdown

### 6.1 `sniffer.py` — Entry Point

**Lines:** 290  
**Responsibility:** Program startup, CLI parsing, interactive menu, component wiring, signal handling.

---

#### Dependency Check

The very first thing `sniffer.py` does — before any other import — is check whether `scapy` and `rich` are installed:

```python
MISSING = []
try:
    import scapy
    from scapy.all import conf
except ImportError:
    MISSING.append("scapy")

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    MISSING.append("rich")

if MISSING:
    print(f"\n[!] Missing packages: {', '.join(MISSING)}")
    print(f"    Install with:  pip install {' '.join(MISSING)}\n")
    sys.exit(1)
```

If either package is missing the program prints a clear error with the exact install command and exits cleanly instead of crashing with a confusing Python traceback. This is particularly important for a presentation environment where the tool needs to fail gracefully.

---

#### `parse_args()` — CLI Argument Parser

Uses Python's built-in `argparse` module to define and parse all command-line arguments:

| Argument | Short | Type | Default | Purpose |
|---|---|---|---|---|
| `--interface` | `-i` | str | None | Network interface name |
| `--filter` | `-f` | choice | `all` | Protocol filter |
| `--port` | — | int | None | Port number filter |
| `--src` | — | str | None | Source IP filter |
| `--dst` | — | str | None | Destination IP filter |
| `--count` | `-c` | int | `0` | Packet count limit (0 = unlimited) |
| `--output` | `-o` | str | None | Output file base name |
| `--verbose` | `-v` | flag | False | Show full payload dump |
| `--list-interfaces` | — | flag | False | Print interfaces and exit |
| `--stats` | — | flag | False | Print last session stats and exit |
| `--no-color` | — | flag | False | Disable colour output |

`argparse` automatically generates a `--help` page and validates argument types (e.g. `--count` must be an integer, `--filter` must be one of the allowed choices).

---

#### `check_root()` — Privilege Verification

Packet sniffing requires raw socket access, which the operating system restricts to privileged users:

```python
def check_root():
    if os.name == "nt":                             # Windows
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            console.print("[bold red][!] Run as Administrator on Windows.[/bold red]")
            sys.exit(1)
    else:                                            # Linux / macOS
        if os.geteuid() != 0:
            console.print("[bold red][!] Run with sudo on Linux/macOS.[/bold red]")
            sys.exit(1)
```

On Linux and macOS, `os.geteuid()` returns `0` if the process is running as root. On Windows, `ctypes.windll.shell32.IsUserAnAdmin()` checks for Administrator privileges. If either check fails, the program prints an actionable error message and exits immediately.

---

#### `interactive_menu()` — Guided Setup Wizard

When the user runs `python sniffer.py` with no arguments, this function takes over and asks five questions in sequence:

1. **Interface selection** — lists all interfaces with IP and MAC, asks the user to pick by number (Enter accepts the default).
2. **Protocol filter** — lists all 10 supported protocols, asks the user to pick (Enter = `all`).
3. **Packet count** — asks for a number (0 or Enter = unlimited).
4. **Verbose mode** — yes/no for payload dump.
5. **Output file** — optional base filename for saving to disk.

The responses are assembled into an `Args` object with the same attribute names as `argparse` would produce, so the rest of `main()` works identically whether arguments came from the CLI or the interactive menu.

---

#### `main()` — Wiring & Startup

The `main()` function is the orchestrator. It:

1. Parses arguments.
2. Handles the two early-exit flags (`--list-interfaces`, `--stats`).
3. Calls `check_root()`.
4. Runs the interactive menu if no interface was given.
5. Instantiates all six component objects:
   - `FilterEngine` — with protocol, port, src_ip, dst_ip
   - `Statistics` — no arguments (starts timing immediately)
   - `Exporter` — only if `--output` was given, otherwise `None`
   - `Display` — with verbose and no_color flags
   - `PacketCapture` — receives all the above as dependencies
6. Registers the `shutdown()` signal handler.
7. Calls `display.print_capture_header()` to print the session banner.
8. Calls `capture.start()` which blocks until stopped.

---

#### Shutdown Handler

```python
def shutdown(sig, frame):
    console.print("\n\n[bold yellow][*] Stopping capture...[/bold yellow]")
    capture.stop()
    stats.print_summary()
    if exporter:
        exporter.finalise()
        console.print(f"[bold green][✓] Saved:[/bold green] {exporter.pcap_path}  |  {exporter.json_path}")
    console.print("[bold cyan][*] NetSniff session ended.[/bold cyan]\n")
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)
```

`SIGINT` fires when the user presses `Ctrl+C`. `SIGTERM` fires when the OS shuts down or when the process is killed externally. Both are handled the same way: stop capture → print summary → finalise files → exit. This guarantees that output files are always properly closed and that the session summary always prints, even if the program is killed suddenly.

---

### 6.2 `core/capture.py` — Capture Engine

**Lines:** 93  
**Class:** `PacketCapture`  
**Responsibility:** Wraps Scapy's `sniff()` and routes each packet through the pipeline.

---

#### Constructor

```python
def __init__(self, interface, filters, stats, display, exporter, count=0):
    self.interface = interface
    self.filters   = filters
    self.stats     = stats
    self.display   = display
    self.exporter  = exporter
    self.count     = count
    self._stopped  = threading.Event()
    self._captured = 0
```

`threading.Event()` is a thread-safe boolean flag. Setting it with `self._stopped.set()` signals the sniff loop to exit at the next opportunity.

---

#### `start()` — The Sniff Loop

```python
def start(self):
    bpf = self.filters.build_bpf()

    sniff(
        iface=self.interface,
        filter=bpf,
        prn=self._process_packet,
        count=self.count,
        store=False,
        stop_filter=lambda p: self._stopped.is_set(),
    )
```

Key parameters explained:

- `iface` — which network card to listen on.
- `filter` — a BPF string handed to the kernel; packets that don't match never reach Python.
- `prn` — a callback function called once per matching packet.
- `count` — Scapy stops automatically after this many packets; `0` means run forever.
- `store=False` — critically important: tells Scapy **not** to buffer packets in a RAM list. Without this, a long capture would consume gigabytes of memory.
- `stop_filter` — a function checked after each packet; returns `True` to stop.

---

#### `_process_packet()` — Per-Packet Pipeline

```python
def _process_packet(self, pkt):
    if not self.filters.match(pkt):
        return

    self._captured += 1
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    self.stats.update(pkt, ts)
    self.display.print_packet(pkt, ts, self._captured)

    if self.exporter:
        self.exporter.write_packet(pkt, ts)

    if self.count and self._captured >= self.count:
        self._stopped.set()
```

The timestamp `%H:%M:%S.%f` with `[:-3]` gives millisecond precision (e.g., `14:30:05.482`). The pipeline sequence is always: filter → stats → display → export. If any stage raises an exception it can be caught without breaking the loop.

---

### 6.3 `core/filters.py` — Filter Engine

**Lines:** 124  
**Class:** `FilterEngine`  
**Responsibility:** Converts user-friendly filter options into kernel-level BPF strings and performs Python-level secondary matching.

---

#### The BPF Mapping Table

```python
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
```

Each user-facing protocol name maps to a BPF expression. `"all"` maps to an empty string, which means no BPF filter — all traffic passes.

---

#### `build_bpf()` — BPF String Builder

```python
def build_bpf(self) -> str:
    parts = []

    base = PROTO_BPF.get(self.protocol, "")
    if base:
        parts.append(base)

    if self.port and self.protocol not in PROTO_PORTS:
        parts.append(f"port {self.port}")

    if self.src_ip:
        parts.append(f"src host {self.src_ip}")
    if self.dst_ip:
        parts.append(f"dst host {self.dst_ip}")

    return " and ".join(parts)
```

Examples of what this produces:

| User input | BPF string output |
|---|---|
| `-f tcp` | `"tcp"` |
| `-f http` | `"tcp port 80"` |
| `-f dns` | `"udp port 53"` |
| `-f tcp --port 8080` | `"tcp and port 8080"` |
| `-f all --src 192.168.1.5` | `"src host 192.168.1.5"` |
| `-f tcp --src 1.2.3.4 --dst 5.6.7.8` | `"tcp and src host 1.2.3.4 and dst host 5.6.7.8"` |

The parts are joined with `" and "` which is valid BPF syntax meaning all conditions must be true simultaneously.

---

#### `match()` — Python-Level Secondary Check

BPF handles the heavy lifting, but the `match()` method performs a secondary Python-level check for IP addresses. This is a defensive measure — it ensures that edge cases where BPF passes a packet that shouldn't be displayed are caught before it reaches the terminal:

```python
def match(self, pkt) -> bool:
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
            return False
    return True
```

This also handles IPv6 addresses, which the BPF `host` keyword handles differently across platforms.

---

### 6.4 `core/display.py` — Display Engine

**Lines:** 280  
**Class:** `Display`  
**Responsibility:** Formats every captured packet into a readable, colour-coded terminal line using Rich.

---

#### Colour Palette

```python
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
```

Every protocol has a unique, instantly recognisable colour. At a glance, a security analyst can see the protocol distribution of traffic just by the colours on screen — no need to read every word.

---

#### Port Label Lookup

```python
PORT_LABELS = {
    20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "TELNET",
    25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    445: "SMB", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    6379: "Redis", 8080: "HTTP-ALT", 8443: "HTTPS-ALT",
    27017: "MongoDB",
}
```

When displaying TCP or UDP packets, port numbers are looked up in this dictionary so instead of `192.168.1.5:443` you see `192.168.1.5:HTTPS`. This dramatically improves readability during a live capture.

---

#### `print_packet()` — Protocol Dispatcher

```python
def print_packet(self, pkt, ts: str, num: int):
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
```

This is a priority-ordered dispatch chain. DNS is checked before TCP/UDP because DNS packets contain both a UDP layer and a DNS layer — checking DNS first ensures they are displayed as DNS rather than plain UDP. ARP is checked first because it has no IP layer at all.

---

#### TCP Printer — `_print_tcp()`

The TCP printer does several things:

1. Extracts IP and TCP layers from the Scapy packet object.
2. Reads source and destination ports.
3. Checks if either port is 80 or 443 to label the packet as HTTP or HTTPS.
4. Calls `_tcp_flags()` to decode the flags integer into a human-readable string.
5. Formats source as `IP:PORT_LABEL` (e.g., `192.168.1.5:HTTP`).
6. Calls `_print_row()` with the colour appropriate for the detected sub-protocol.
7. If HTTP and payload is present, calls `_print_http_preview()`.
8. If verbose mode is on, calls `_print_payload()` for hex+ASCII dump.

---

#### TCP Flag Decoder — `_tcp_flags()`

```python
@staticmethod
def _tcp_flags(flags) -> str:
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
```

Scapy represents TCP flags as an object whose string representation contains the single-character codes that are set (e.g., `"SA"` for SYN+ACK, `"PA"` for PSH+ACK). This method maps those codes to their full names and joins them with `|` (e.g., `"SYN|ACK"`, `"PSH|ACK"`, `"FIN"`).

---

#### Hex + ASCII Payload Dump — `_print_payload()`

In verbose mode (`-v`), every packet with a Raw layer shows a dump like this:

```
── Payload ──────────────────────────────
0000  47 45 54 20 2F 20 48 54 54 50 2F 31 2E 31 0D 0A  GET / HTTP/1.1..
0010  48 6F 73 74 3A 20 65 78 61 6D 70 6C 65 2E 63 6F  Host: example.co
0020  6D 0D 0A 43 6F 6E 6E 65 63 74 69 6F 6E 3A 20 6B  m..Connection: k
────────────────────────────────────────
```

The dump processes the payload in 16-byte chunks. For each chunk it generates a hex representation (two uppercase hex digits per byte, space-separated) and an ASCII representation (printable ASCII characters shown as-is, everything else shown as `.`). This format is identical to what Wireshark and `xxd` produce, making it immediately recognisable to security professionals.

---

### 6.5 `core/stats.py` — Statistics Engine

**Lines:** 230  
**Class:** `Statistics`  
**Responsibility:** Accumulates per-packet counters and produces a rich end-of-session summary.

---

#### Data Structures

The `Statistics` class uses Python's `Counter` and `defaultdict` from the `collections` module:

```python
self.total_packets = 0
self.total_bytes   = 0
self.proto_counts  = Counter()       # {"TCP": 842, "DNS": 201, ...}
self.proto_bytes   = Counter()       # {"TCP": 1231448, ...}
self.src_ips       = Counter()       # {"192.168.1.5": 712, ...}
self.dst_ips       = Counter()       # {"8.8.8.8": 201, ...}
self.src_ports     = Counter()       # {80: 412, 443: 318, ...}
self.dst_ports     = Counter()       # {80: 198, 443: 201, ...}
self.tcp_flags     = Counter()       # {"ACK": 612, "SYN": 42, ...}
self.size_bins     = Counter()       # {"<64 B": 23, "64-127 B": 512, ...}
self._sec_packets  = defaultdict(int) # {0: 5, 1: 8, 2: 12, ...}
self._sec_bytes    = defaultdict(int) # {0: 3200, 1: 5120, ...}
```

`Counter` is a dictionary subclass designed for counting. It supports `.most_common(n)` which returns the n most frequent items sorted by count — perfect for finding the top 10 talkers or the busiest ports.

`defaultdict(int)` is a dictionary where missing keys automatically get a default value of `0` instead of raising a `KeyError`. This is ideal for the per-second time buckets.

---

#### `update()` — Per-Packet Statistics Update

Called once per accepted packet. In sequence it:

1. Adds packet size to `total_bytes` and increments `total_packets`.
2. Bins the packet size into one of five ranges (`<64 B`, `64-127 B`, `128-511 B`, `512-1023 B`, `1024+ B`).
3. Increments the current second's bucket in `_sec_packets` and `_sec_bytes`.
4. Extracts the IP layer and increments source/destination IP counters.
5. Identifies the protocol layer and increments the appropriate protocol counter and byte counter.
6. For TCP packets, also extracts and counts each flag character present in the flags field.

---

#### `print_summary()` — End-of-Session Report

Called when Ctrl+C is pressed. Produces six Rich-formatted sections:

**Section 1 — Session Overview Panel:**
```
Session Duration : 0:02:35
Total Packets    : 1,284
Total Bytes      : 1,547,392 B  (1,511.1 KB)
Avg Throughput   : 8.3 pkt/s  |  9.7 KB/s
```
Duration uses `timedelta` for clean formatting. Throughput is calculated as `total_packets / elapsed_seconds` and `(total_bytes / 1024) / elapsed_seconds`.

**Section 2 — Protocol Breakdown Table:** Each protocol row includes an inline ASCII bar chart where one `█` block represents 5% of traffic.

**Section 3 — Top Source IPs:** Top 10 source addresses by packet count using `Counter.most_common(10)`.

**Section 4 — Top Destination IPs:** Top 10 destination addresses.

**Section 5 — Top Destination Ports:** Top 10 ports with their service name label.

**Section 6 — TCP Flag Counts:** How many packets contained each TCP flag.

**Section 7 — Packet Size Distribution:** How traffic was distributed across size ranges.

**Section 8 — ASCII Sparkline:**

```python
bars  = "▁▂▃▄▅▆▇█"
vals  = [self._sec_packets[s] for s in sorted(self._sec_packets)]
mx    = max(vals) if vals else 1
spark = "".join(bars[min(int(v / mx * (len(bars) - 1)), len(bars) - 1)] for v in vals)
```

This maps each second's packet count to one of 8 Unicode block characters (`▁` through `█`) proportional to the peak rate. The resulting one-line string visualises the entire capture session's traffic shape — bursts, idle periods, and peaks — at a glance.

---

### 6.6 `core/export.py` — Export Engine

**Lines:** 250  
**Class:** `Exporter`  
**Responsibility:** Writes captured packets to `.pcap` and `.json` files incrementally.

---

#### Output Path Resolution

```python
if os.sep not in base_name and "/" not in base_name:
    out_dir = Path.home() / "Desktop"
else:
    out_dir = Path(base_name).parent
    base_name = Path(base_name).name
```

If the user gives a bare filename like `capture1`, the files are saved to the Desktop. If they give a full path like `/home/user/captures/session1`, that path is respected. `Path.home()` works correctly on Windows (`C:\Users\name\`), Linux (`/home/name/`), and macOS (`/Users/name/`).

---

#### PCAP Output

```python
self._pcap_writer = PcapWriter(self.pcap_path, append=False, sync=True)
```

`PcapWriter` from Scapy writes the libpcap binary format. With `sync=True`, each packet is flushed to disk immediately — no buffering. This means the file is always valid and readable in Wireshark even if the program crashes mid-capture. `append=False` creates a fresh file each run.

```python
def _write_pcap(self, pkt):
    self._pcap_writer.write(pkt)
```

Each packet is written as a raw binary record containing the packet's timestamp, captured length, original length, and raw bytes. This is exactly the format Wireshark, tcpdump, and every other pcap-aware tool can read.

---

#### JSON Output

```python
# File opened in write mode with JSON array started:
self._json_file.write("[\n")

# Each packet:
comma = "" if self._first else ","
self._json_file.write(f"{comma}\n{json.dumps(record, indent=2)}")
self._json_file.flush()
```

The JSON file is an array where each element is a packet object. The first packet gets no leading comma; all subsequent ones get a comma prepended. After each packet, `flush()` is called to write the data to disk immediately. This technique produces valid JSON incrementally without loading everything into memory first.

---

#### `_packet_to_dict()` — Packet Serialiser

This static method converts a Scapy packet into a plain Python dictionary. It examines the packet layer by layer:

- **Ethernet** → `src`, `dst`, `type` (hex)
- **ARP** → `op` (request/reply), `src_ip`, `dst_ip`, `src_mac`, `dst_mac`
- **IP** → `version`, `src`, `dst`, `ttl`, `proto`, `id`, `flags`, `len`, `chksum` (hex)
- **IPv6** → `src`, `dst`, `hop_limit`, `next_hdr`
- **TCP** → `sport`, `dport`, `seq`, `ack`, `flags`, `window`, `chksum` (hex)
- **UDP** → `sport`, `dport`, `len`, `chksum` (hex)
- **ICMP** → `type` (name), `code`, `id`, `seq`
- **DNS** → `id`, `qr` (query/response), `questions` list, `answers` list
- **Raw** → `length`, `hex` (first 64 bytes), `ascii` (printable representation)

The resulting JSON is self-documenting — anyone reading the file can understand every field without additional documentation.

---

#### `finalise()` — Clean File Closing

```python
def finalise(self):
    try:
        self._pcap_writer.close()
    except Exception:
        pass

    try:
        self._json_file.write("\n]\n")
        self._json_file.close()
    except Exception:
        pass
```

Called from the shutdown handler. Closes the pcap writer (which flushes any remaining buffer) and writes the closing `]` to the JSON array, making it a valid JSON document. Exceptions are silently caught because if the shutdown is called due to a crash, the files may already be in an inconsistent state — we try our best without crashing the shutdown sequence.

---

### 6.7 `core/interfaces.py` — Interface Manager

**Lines:** 93  
**Class:** `InterfaceManager`  
**Responsibility:** Discovers, validates, and displays available network interfaces.

---

#### `list_interfaces()` — Interface Discovery

```python
def list_interfaces(self) -> dict:
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
```

`get_if_list()` returns all interface names from Scapy's internal interface table, which reads from the OS. `get_if_addr()` retrieves the IPv4 address. `get_if_hwaddr()` retrieves the MAC address. Both are wrapped in `try/except` because some virtual or loopback interfaces may not have these attributes on all platforms.

An interface with no IP address is marked as `is_up=False` (shown as "DOWN" in the table). It can still be sniffed on (useful for promiscuous mode or tap interfaces) — it just doesn't have an active IPv4 assignment.

---

#### `get_default_interface()` — Default Interface

```python
def get_default_interface(self) -> str:
    try:
        return conf.iface
    except Exception:
        return "eth0"
```

`conf.iface` is Scapy's auto-detected best interface — typically the one with the default route. It falls back to `"eth0"` if detection fails.

---

#### `print_interfaces()` — Rich Table Output

Produces a table with six columns: number, interface name, IP address, MAC address, status (UP/DOWN), and a `★` marker for the default interface. This is displayed when `--list-interfaces` is used, and also at the top of the interactive menu.

---

## 7. Protocol Coverage Deep Dive

### Ethernet (Layer 2)

Every captured packet starts with an Ethernet frame. The Ethernet layer contains:
- **Source MAC** — hardware address of the sending network card.
- **Destination MAC** — hardware address of the receiving card (or broadcast `ff:ff:ff:ff:ff:ff`).
- **EtherType** — a 16-bit number identifying the next protocol (0x0800 = IPv4, 0x0806 = ARP, 0x86DD = IPv6).

NetSniff stores Ethernet details in the JSON export. The terminal display focuses on higher-level protocols.

### ARP (Address Resolution Protocol)

ARP operates at Layer 2/3. It maps IP addresses to MAC addresses on a local network. Two types:

- **ARP Request (op=1):** "Who has 192.168.1.1? Tell 192.168.1.5" — broadcast to all devices.
- **ARP Reply (op=2):** "192.168.1.1 is at aa:bb:cc:dd:ee:ff" — unicast back to the requester.

ARP is important in security because ARP Spoofing attacks poison ARP caches to redirect traffic through an attacker's machine (man-in-the-middle attack). NetSniff shows both the IP and MAC addresses in every ARP line.

### IP / IPv6 (Layer 3)

The IP header contains:
- **src/dst** — source and destination IP addresses.
- **TTL** (Time To Live) — decremented by each router; reaches 0 → packet dropped. Useful for tracing routes.
- **Protocol** — identifies the next layer (6=TCP, 17=UDP, 1=ICMP).
- **Flags** — DF (Don't Fragment), MF (More Fragments).
- **ID** — used to reassemble fragmented packets.

### TCP (Layer 4)

TCP is a connection-oriented protocol. The header contains:
- **sport/dport** — source and destination port numbers.
- **seq/ack** — sequence and acknowledgment numbers for ordering and reliability.
- **flags** — 8 flag bits that control the connection state.
- **window** — how much data the receiver can accept.

**TCP Flags reference:**

| Flag | Name | Meaning |
|---|---|---|
| SYN | Synchronise | Initiates a connection (first packet of 3-way handshake) |
| ACK | Acknowledge | Confirms received data |
| FIN | Finish | Graceful connection close |
| RST | Reset | Abrupt connection termination (error or rejection) |
| PSH | Push | Send buffered data immediately |
| URG | Urgent | Urgent data present |
| ECE | ECN-Echo | Congestion notification |
| CWR | Congestion Window Reduced | Sender reduced window in response |

A typical TCP connection looks like: `SYN` → `SYN|ACK` → `ACK` (three-way handshake), then data flows as `PSH|ACK` packets.

### UDP (Layer 4)

UDP is connectionless and lightweight — no handshake, no sequence numbers, no acknowledgments. Faster but unreliable. Used by DNS, DHCP, streaming video, and VoIP. The header contains only sport, dport, length, and checksum.

### ICMP

ICMP carries control messages. Common types:
- **Type 8** — Echo Request (ping sends this)
- **Type 0** — Echo Reply (the response to ping)
- **Type 3** — Destination Unreachable (with code identifying why)
- **Type 11** — Time Exceeded (TTL reached 0; used by `traceroute`)

### DNS

DNS translates domain names to IP addresses. It runs over UDP port 53 (and TCP for large responses). NetSniff decodes:
- **Queries:** extracts `qname` (the domain being looked up) from the `qd` (question) section.
- **Responses:** walks the `an` (answer) resource records and extracts `rdata` (the resolved IP addresses).

### HTTP / HTTPS

HTTP runs over TCP port 80. HTTPS runs over TCP port 443. NetSniff identifies both by checking the TCP port numbers. For HTTP, it reads the Raw payload and displays the first line of the request/response (e.g., `GET /index.html HTTP/1.1` or `HTTP/1.1 200 OK`). HTTPS traffic is encrypted, so only the TCP metadata is visible — not the payload content.

---

## 8. BPF — The Two-Layer Filtering System

One of the most important design decisions in NetSniff is the two-layer filtering system.

### Layer 1: Kernel-Level BPF Filter

BPF (Berkeley Packet Filter) is a mini-language built into every modern operating system's network stack. When you pass a BPF expression to libpcap, it is compiled into bytecode and executed **in the kernel** — before the packet is copied to user space.

```
All network traffic
      │
      ▼
┌─────────────────────────────────────┐
│         KERNEL SPACE                │
│                                     │
│   BPF: "tcp port 80"                │
│                                     │
│   For each packet:                  │
│     if match → copy to user space   │
│     if no match → drop (free)       │
└──────────────┬──────────────────────┘
               │  Only matching packets
               ▼
         User Space (Python)
```

This is critical for performance. On a busy network interface, thousands of packets per second may be arriving. Without BPF, Python would receive every single one, wasting CPU time on packets you don't care about. With BPF, the kernel discards them at near-zero cost.

### Layer 2: Python-Level Secondary Check

After BPF, the `FilterEngine.match()` method performs a second check. This is redundant with BPF for most cases but serves as:

1. **A safety net** for edge cases where BPF and Python's interpretation differ.
2. **IPv6 support** — BPF `host` matching behaves differently on some platforms for IPv6 addresses.
3. **Extensibility** — future filters that BPF cannot express (e.g., filtering by HTTP method or DNS record type) can be added here without changing the BPF layer.

### BPF Examples

```
tcp                           All TCP traffic
udp port 53                   DNS queries/responses
tcp port 80                   HTTP
tcp port 443                  HTTPS
src host 192.168.1.5          Traffic FROM this IP
dst host 8.8.8.8              Traffic TO Google DNS
tcp and src host 10.0.0.1     TCP from a specific host
tcp port 80 and dst host 1.1.1.1   HTTP to Cloudflare
```

---

## 9. Output Formats Explained

### Terminal Output (Live)

Each packet is displayed as a single 100-character-wide line:

```
    #       Time     Proto           Source         Destination  Info
─────────────────────────────────────────────────────────────────────
    1  14:30:00.123   HTTP  192.168.1.5:52341  142.250.80.14:HTTP  Flags=[SYN]  Seq=0  74B
  HTTP: GET / HTTP/1.1
    2  14:30:00.215    DNS    192.168.1.5:DNS        8.8.8.8:DNS  Query: www.google.com.
    3  14:30:01.003   ICMP    192.168.1.5        192.168.1.1  Echo Request  Code=0  ID=1  Seq=1
    4  14:30:01.052    ARP  192.168.1.5 (aa:bb)  192.168.1.1 (?)  Who has 192.168.1.1?
```

### `.pcap` File (Binary)

The libpcap binary format. File structure:

```
[Global Header — 24 bytes]
  Magic number: 0xA1B2C3D4
  Version: 2.4
  Timezone offset: 0
  Timestamp accuracy: 0
  Snapshot length: 65535
  Link type: 1 (Ethernet)

[Packet Record 1]
  Timestamp seconds
  Timestamp microseconds
  Captured length
  Original length
  Raw packet bytes...

[Packet Record 2]
...
```

This file can be opened in Wireshark, analyzed with `tcpdump -r capture.pcap`, processed with `tshark`, or imported into Elasticsearch, Splunk, or Zeek. It is the universal format for packet data.

### `.json` File (Structured Text)

A JSON array where each element is a fully parsed packet:

```json
[
{
  "timestamp": "14:30:00.123",
  "length": 74,
  "layers": ["Ethernet", "IP", "TCP"],
  "ethernet": {
    "src": "aa:bb:cc:dd:ee:ff",
    "dst": "11:22:33:44:55:66",
    "type": "0x800"
  },
  "ip": {
    "version": 4,
    "src": "192.168.1.5",
    "dst": "142.250.80.14",
    "ttl": 64,
    "proto": 6,
    "id": 12345,
    "flags": "DF",
    "len": 60,
    "chksum": "0x3a2f"
  },
  "tcp": {
    "sport": 52341,
    "dport": 80,
    "seq": 0,
    "ack": 0,
    "flags": "S",
    "window": 65535,
    "chksum": "0x8f2a"
  }
},
...
]
```

Both files are written to the Desktop unless a full path is specified. Both are written incrementally — one packet at a time — so data is preserved even if the program is force-killed.

---

## 10. Session Statistics System

The `Statistics` class produces eight distinct measurements at the end of every session. Here is what each tells you:

### 1. Session Duration

Calculated as `time.time() - self._start_time` and formatted with `timedelta`. Shows exactly how long the capture ran.

### 2. Total Packets & Bytes

Raw counts. Byte count is also shown in KB for readability. These are the most basic metrics of network activity.

### 3. Average Throughput

```python
pps  = total_packets / elapsed_seconds   # packets per second
kbps = (total_bytes / 1024) / elapsed_seconds  # kilobytes per second
```

Throughput tells you how busy the network segment is. A home network idle might show 2–5 pkt/s. A loaded LAN might show 1000+ pkt/s.

### 4. Protocol Breakdown

Shows what fraction of traffic each protocol represents. Typical findings on a home network:
- TCP dominates (web browsing, streaming)
- DNS is frequent but small (many lookups)
- UDP appears for video calls, gaming, NTP
- ICMP appears only when ping is running
- ARP appears periodically as devices resolve local addresses

### 5. Top Source / Destination IPs

Identifies the most active talkers and listeners. This can reveal:
- Which device is generating the most traffic
- Which external server is receiving the most requests
- Unexpected communication (e.g., an IP that shouldn't be there)

### 6. Top Destination Ports

Shows which services are being accessed most. Port 443 dominates modern traffic. Unusual ports (e.g., 3389 = RDP) appearing frequently could indicate remote access or a scan.

### 7. TCP Flag Frequency

Reveals connection patterns:
- Very high SYN count with few ACKs → possible SYN flood or port scan
- High RST count → many refused connections or network instability
- Balanced SYN/FIN → normal connection lifecycle

### 8. Packet Size Distribution

Shows whether traffic consists mostly of small control packets or large data transfers:
- Mostly `<64 B` → control traffic, ACKs, DNS, ARP
- Mostly `1024+ B` → file transfers, streaming, large downloads
- Mix → typical web browsing

### 9. Packets-per-Second Sparkline

A single line of Unicode block characters showing the traffic rate over time. Peaks and valleys reveal:
- When downloads happened
- When the network was idle
- Whether traffic was steady or bursty

---

## 11. CLI Reference

### Full Argument List

```
usage: sniffer.py [-h] [-i INTERFACE] [-f {tcp,udp,icmp,arp,dns,http,https,ftp,ssh,all}]
                  [--port PORT] [--src SRC] [--dst DST] [-c COUNT] [-o OUTPUT]
                  [-v] [--list-interfaces] [--stats] [--no-color]

Options:
  -i, --interface       Network interface (eth0, wlan0, lo, ...)
  -f, --filter          Protocol filter (default: all)
  --port                Filter by port number
  --src                 Filter by source IP
  --dst                 Filter by destination IP
  -c, --count           Max packets (0 = unlimited, default: 0)
  -o, --output          Save to FILENAME.pcap and FILENAME.json on Desktop
  -v, --verbose         Show hex+ASCII payload for every packet
  --list-interfaces     List all interfaces and exit
  --stats               Show session statistics (requires prior session)
  --no-color            Disable colour output (for piping to files)
  -h, --help            Show help and exit
```

### Common Command Patterns

```bash
# Quick start — see everything on the default interface
sudo python sniffer.py

# Watch only DNS (useful to see which domains are being looked up)
sudo python sniffer.py -i eth0 -f dns

# Monitor HTTP traffic with payload preview
sudo python sniffer.py -i eth0 -f http

# Capture 100 packets then stop, save to files
sudo python sniffer.py -i eth0 -c 100 -o mysession

# Watch traffic between two specific hosts
sudo python sniffer.py -i eth0 --src 192.168.1.5 --dst 8.8.8.8

# Full verbose dump of HTTPS traffic (shows TCP metadata; payload is encrypted)
sudo python sniffer.py -i eth0 -f https -v

# See all active interfaces
sudo python sniffer.py --list-interfaces

# Log everything to a file (pipe, no colour)
sudo python sniffer.py -i eth0 --no-color > capture_log.txt
```

---

## 12. How a Packet Sniffer Works — Conceptual Explanation

### Promiscuous Mode

Normally, a network card only delivers packets addressed to its own MAC address to the operating system. A packet sniffer needs to see all packets on the network segment, including ones addressed to other devices.

To achieve this, the network card is placed into **promiscuous mode**, where it accepts and delivers every frame it receives — regardless of the destination MAC address. libpcap and Scapy handle this automatically when a capture is started.

> **Note:** On a switched network (which all modern networks are), promiscuous mode only shows traffic that reaches your port — broadcasts, multicasts, and traffic to/from your machine. To see all traffic on a switch, you need a SPAN/mirror port or you need to perform ARP spoofing.

### The Copy-on-Capture Model

When libpcap captures a packet, it does **not** intercept or modify the packet. It makes a **copy** of the frame's bytes at the point where they pass through the kernel's network stack. The original packet continues to its destination normally.

This is why a packet sniffer is sometimes called a **passive** or **non-intrusive** tool — it observes without interfering.

```
Incoming frame
     │
     ├──────────────────────► Copy to libpcap buffer → Python → NetSniff
     │
     ▼
Normal OS network stack processing → application receives packet
```

### Raw Sockets

Under the hood, libpcap opens a raw socket — a special type of socket that receives packets at the Ethernet frame level, before the OS has stripped any headers. Raw sockets require root/Administrator privileges because they give access to all network traffic, which could be used to read other users' unencrypted data.

---

## 13. Ethical & Legal Disclaimer

> ⚠️ **This software is built exclusively for educational and authorized use.**

The legality of packet sniffing depends entirely on:

1. **Ownership** — you own the device and the network, OR
2. **Written authorization** — the network owner has explicitly authorized the capture.

Sniffing traffic on a network you don't own or haven't been authorized to test is:

- **Illegal in Pakistan** under PECA 2016 (Prevention of Electronic Crimes Act) — Section 3 (Unauthorized Access to Information Systems) and Section 4 (Unauthorized Copying or Transmission of Data).
- **Illegal in the USA** under the Computer Fraud and Abuse Act (CFAA) and the Electronic Communications Privacy Act (ECPA).
- **Illegal in the EU** under the Network and Information Security Directive and national implementations.
- **Illegal in the UK** under the Computer Misuse Act 1990.

**Acceptable uses for this tool:**
- Capturing traffic on your own home network for learning.
- Capturing loopback traffic on your own machine (`-i lo`).
- Authorized lab environments and cybersecurity courses.
- Authorized penetration testing with written scope agreements.

**Not acceptable:**
- Capturing traffic on a workplace network without IT department authorization.
- Capturing traffic on a public WiFi network.
- Capturing traffic from other users' devices.

---

## 14. Setup & Usage Guide

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Root/Administrator access

### Platform-Specific Requirements

**Linux:**
```bash
sudo apt install libpcap-dev    # Debian/Ubuntu
sudo dnf install libpcap-devel  # Fedora/RHEL
sudo pacman -S libpcap          # Arch
```

**macOS:**
libpcap is built in. No extra installation needed.

**Windows:**
Download and install Npcap from https://npcap.com before installing Scapy. Run Command Prompt as Administrator.

### Installation

```bash
pip install -r requirements.txt
```

### Running the Tool

**Option A — Interactive (recommended for beginners):**
```bash
sudo python sniffer.py
```
Follow the prompts.

**Option B — Full CLI:**
```bash
sudo python sniffer.py -i eth0 -f dns -c 50 -o dns_session
```

### Stopping the Tool

Press `Ctrl+C`. The tool will:
1. Stop capturing immediately.
2. Print the full session statistics summary.
3. If `-o` was used, close and save the output files.
4. Print the file paths.
5. Exit cleanly.

### Viewing Output in Wireshark

1. Open Wireshark.
2. File → Open → select `capture.pcap` from the Desktop.
3. All packets appear with Wireshark's full dissection and colour coding.

---

## 15. Conclusion

NetSniff demonstrates the complete lifecycle of network packet capture in a well-structured, readable, and educationally transparent Python project. By building every component from scratch — rather than using a single-function black-box — the project makes visible the full chain of decisions and mechanisms that professional network analysis tools rely on.

The key technical concepts covered by this project include:

- **Raw socket programming** — how operating systems expose network traffic to applications.
- **BPF (Berkeley Packet Filter)** — kernel-level packet filtering for performance.
- **Protocol stack parsing** — reading Ethernet, IP, TCP, UDP, ICMP, DNS, and HTTP headers.
- **Multi-threading** — running independent tasks (capture, statistics, display) safely.
- **Binary file formats** — the libpcap format used by Wireshark and every professional tool.
- **Incremental file writing** — keeping output files consistent even during long captures.
- **CLI design** — building flexible, self-documenting command-line tools with argparse.
- **Signal handling** — graceful shutdown on Ctrl+C and OS-level SIGTERM.
- **Terminal UI** — using Rich for structured, colour-coded output that scales across terminal sizes.

From an educational perspective, the project reinforces the core principle of cybersecurity: **you cannot defend what you don't understand**. Understanding exactly how a packet sniffer works — at the socket level, at the protocol decoding level, and at the file format level — is the foundation for understanding how network monitoring, intrusion detection, and traffic analysis work in the real world.

---

*Report ends.*  
*For usage instructions, refer to the `README.md` file or run `python sniffer.py --help`.*
