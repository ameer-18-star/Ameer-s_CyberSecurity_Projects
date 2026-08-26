# NetSniff — Educational Network Packet Sniffer

> **For authorized use on your own network or lab environment only.**
> Capturing network traffic without permission is illegal in most countries.

---

## Features

| Feature | Detail |
|---|---|
| **Live packet capture** | Captures all traffic on a chosen network interface in real time |
| **Protocol detection** | Identifies Ethernet, ARP, IP, IPv6, TCP, UDP, ICMP, DNS, HTTP, HTTPS, FTP, SSH |
| **Protocol filter** | Filter by protocol name at startup (`-f tcp`, `-f dns`, `-f http`, etc.) |
| **Port filter** | Capture only traffic on a specific port (`--port 443`) |
| **IP filter** | Filter by source IP (`--src`), destination IP (`--dst`), or both |
| **Packet count** | Stop automatically after N packets (`-c 100`) |
| **Verbose / payload dump** | Show hex + ASCII payload of every packet (`-v`) |
| **HTTP preview** | Shows the first line of HTTP requests/responses automatically |
| **DNS decoder** | Decodes DNS queries and responses into human-readable names |
| **TCP flag decoder** | Shows SYN / ACK / FIN / RST / PSH / URG flags on every TCP packet |
| **PCAP export** | Saves capture to a `.pcap` file openable in Wireshark (`-o filename`) |
| **JSON export** | Saves every packet as a structured JSON record (`-o filename`) |
| **Session statistics** | End-of-session summary: protocol breakdown, top IPs, top ports, throughput |
| **ASCII sparkline** | Packets-per-second graph printed at the end of every session |
| **Interface listing** | Lists all network interfaces with IP, MAC, and status (`--list-interfaces`) |
| **Interactive menu** | Run without arguments for a guided setup wizard |
| **BPF kernel filter** | Passes BPF expressions to the kernel — only matching packets enter Python |
| **Graceful shutdown** | Ctrl+C saves all data and prints the summary before exiting |
| **Cross-platform** | Works on Linux, macOS, and Windows (with Npcap) |

---

## Installation

### Prerequisites

- Python 3.8 or higher
- `pip` package manager
- **Linux / macOS:** run with `sudo`
- **Windows:** install [Npcap](https://npcap.com/) first, then run as Administrator

### Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs two packages:
- `scapy` — packet capture and parsing
- `rich` — colored terminal output

### Linux: install libpcap (if not already present)

```bash
# Debian / Ubuntu
sudo apt install libpcap-dev

# Fedora / RHEL
sudo dnf install libpcap-devel

# Arch
sudo pacman -S libpcap
```

---

## Project Structure

```
packet_sniffer/
│
├── sniffer.py              ← Entry point: CLI args, menu, startup
│
├── requirements.txt        ← Python package dependencies
│
├── README.md               ← This file
│
└── core/
    ├── __init__.py
    ├── capture.py          ← PacketCapture: Scapy sniff() wrapper
    ├── filters.py          ← FilterEngine: BPF builder + Python-level match
    ├── display.py          ← Display: Rich-formatted terminal output
    ├── stats.py            ← Statistics: counters, top-talkers, sparkline
    ├── export.py           ← Exporter: .pcap and .json file writers
    └── interfaces.py       ← InterfaceManager: interface discovery + display
```

---

## Usage

### Basic — interactive menu (no arguments)

```bash
sudo python sniffer.py
```

Launches the guided setup wizard that asks for interface, protocol, count, verbosity, and output file.

### Specify interface

```bash
sudo python sniffer.py -i eth0
sudo python sniffer.py -i wlan0
sudo python sniffer.py -i lo          # loopback (your own machine's traffic)
```

### Protocol filter

```bash
sudo python sniffer.py -i eth0 -f tcp       # TCP only
sudo python sniffer.py -i eth0 -f udp       # UDP only
sudo python sniffer.py -i eth0 -f icmp      # ICMP (ping) only
sudo python sniffer.py -i eth0 -f arp       # ARP only
sudo python sniffer.py -i eth0 -f dns       # DNS queries and responses
sudo python sniffer.py -i eth0 -f http      # HTTP (port 80)
sudo python sniffer.py -i eth0 -f https     # HTTPS (port 443)
sudo python sniffer.py -i eth0 -f ftp       # FTP (port 21)
sudo python sniffer.py -i eth0 -f ssh       # SSH (port 22)
sudo python sniffer.py -i eth0 -f all       # Everything (default)
```

### Port and IP filtering

```bash
sudo python sniffer.py -i eth0 --port 8080          # Any traffic on port 8080
sudo python sniffer.py -i eth0 --src 192.168.1.5    # Packets from this IP
sudo python sniffer.py -i eth0 --dst 8.8.8.8        # Packets to this IP
sudo python sniffer.py -i eth0 --src 10.0.0.1 --dst 10.0.0.2   # Between two IPs
```

### Packet count limit

```bash
sudo python sniffer.py -i eth0 -c 50        # Stop after 50 packets
sudo python sniffer.py -i eth0 -f dns -c 10 # Capture 10 DNS packets
```

### Verbose — full payload dump

```bash
sudo python sniffer.py -i eth0 -v
```

Each packet shows a hex + ASCII dump of its payload (up to 256 bytes).

### Save to file

```bash
sudo python sniffer.py -i eth0 -o capture1
```

Creates two files on your Desktop:
- `capture1.pcap` — binary file, openable in Wireshark
- `capture1.json` — one JSON object per packet

### List interfaces

```bash
sudo python sniffer.py --list-interfaces
```

Shows a table of all interfaces with their IP, MAC, and up/down status.

### Combine options

```bash
sudo python sniffer.py -i eth0 -f tcp --dst 8.8.8.8 -c 20 -v -o test_run
```

Capture 20 TCP packets going to 8.8.8.8, show full payload, save to files.

---

## Sample Output

```
╔══════════════════════════════════════════════════════════════╗
║  NetSniff — Capture Session                                  ║
║  Interface :  eth0                                           ║
║  Filter    :  Protocol: tcp                                  ║
║  Count     :  unlimited                                      ║
║  Output    :  none                                           ║
║  Started   :  2026-07-24  14:30:00                          ║
╚══════════════════════════════════════════════════════════════╝

    #          Time   Proto             Source         Destination  Info
────────────────────────────────────────────────────────────────────────────
    1  14:30:00.123   TCP     192.168.1.5:52341  142.250.80.14:HTTP  Flags=[SYN]  Seq=0
    2  14:30:00.145   TCP    142.250.80.14:HTTP   192.168.1.5:52341  Flags=[SYN|ACK]  Seq=0
  HTTP: GET / HTTP/1.1
    3  14:30:00.201   DNS       192.168.1.5:DNS       8.8.8.8:DNS  Query: www.google.com.
    4  14:30:00.215   DNS          8.8.8.8:DNS    192.168.1.5:DNS  Response: 142.250.80.14
    5  14:30:01.003  ICMP       192.168.1.5       192.168.1.1  Echo Request  Code=0  ID=1  Seq=1
    6  14:30:01.012  ICMP       192.168.1.1       192.168.1.5  Echo Reply  Code=0  ID=1  Seq=1
    7  14:30:01.300   ARP  192.168.1.5 (aa:bb)  192.168.1.1 (?)  Who has 192.168.1.1? Tell 192.168.1.5
```

### End-of-session summary

```
┌─────────────────────────────────────────────────┐
│  ── Session Summary ──                          │
│  Session Duration : 0:02:35                     │
│  Total Packets    : 1,284                       │
│  Total Bytes      : 1,547,392 B  (1,511.1 KB)  │
│  Avg Throughput   : 8.3 pkt/s  |  9.7 KB/s     │
└─────────────────────────────────────────────────┘

Protocol Breakdown
──────────────────
Protocol  Packets    Bytes    Share
TCP         842    1,231,448  ████████ 65.6%
DNS         201      24,522   ██ 15.7%
UDP         156      87,443   ██ 12.1%
ICMP         62      7,440    █  4.8%
ARP          23      1,472       1.8%

Top Source IPs                 Top Destination IPs
──────────────                 ───────────────────
192.168.1.5   712             8.8.8.8        201
192.168.1.1   201             142.250.80.14  198
10.0.0.3       91             192.168.1.1    187

Packets / Second
▁▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▁▂▃▄▅▆▇▆▅▄▃
0s ───────────────────────── 155s
Peak: 24 pkt/s
```

---

## JSON Output Format

Each packet in the `.json` file looks like this:

```json
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
    "flags": "DF",
    "len": 60
  },
  "tcp": {
    "sport": 52341,
    "dport": 80,
    "seq": 0,
    "ack": 0,
    "flags": "S",
    "window": 65535
  }
}
```

---

## Ethical & Legal Notice

- Only use this tool on **networks and devices you own or have explicit written permission to test.**
- Capturing traffic on a network without authorization is a criminal offense under the Computer Fraud and Abuse Act (USA), Computer Misuse Act (UK), Pakistan Electronic Crimes Act (PECA 2016), and equivalent laws worldwide.
- This tool is designed for **education, lab environments, and authorized penetration testing** only.
