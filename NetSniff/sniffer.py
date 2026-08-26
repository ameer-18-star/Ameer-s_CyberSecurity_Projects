"""
╔══════════════════════════════════════════════════════════════╗
║           NetSniff — Educational Network Packet Sniffer      ║
║           For cybersecurity internship / education only.     ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    sudo python sniffer.py                     # interactive menu
    sudo python sniffer.py -i eth0             # specific interface
    sudo python sniffer.py -i eth0 -f tcp      # filter by protocol
    sudo python sniffer.py -i eth0 -c 50       # capture 50 packets
    sudo python sniffer.py -i eth0 --port 80   # filter by port
    sudo python sniffer.py --list-interfaces   # show interfaces
    sudo python sniffer.py -i eth0 -o capture  # save to pcap + json
    sudo python sniffer.py --stats             # show session stats
"""

import sys
import os
import argparse
import signal
import time

# ── Dependency check ──────────────────────────────────────────
MISSING = []
try:
    import scapy
    from scapy.all import conf
except ImportError:
    MISSING.append("scapy")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
except ImportError:
    MISSING.append("rich")

if MISSING:
    print(f"\n[!] Missing packages: {', '.join(MISSING)}")
    print(f"    Install with:  pip install {' '.join(MISSING)}\n")
    sys.exit(1)

from core.capture    import PacketCapture
from core.display    import Display
from core.filters    import FilterEngine
from core.stats      import Statistics
from core.export     import Exporter
from core.interfaces import InterfaceManager

console = Console()

# ── Banner ────────────────────────────────────────────────────
BANNER = """
[bold cyan]
  ███╗   ██╗███████╗████████╗███████╗███╗   ██╗██╗███████╗███████╗
  ████╗  ██║██╔════╝╚══██╔══╝██╔════╝████╗  ██║██║██╔════╝██╔════╝
  ██╔██╗ ██║█████╗     ██║   ███████╗██╔██╗ ██║██║█████╗  █████╗
  ██║╚██╗██║██╔══╝     ██║   ╚════██║██║╚██╗██║██║██╔══╝  ██╔══╝
  ██║ ╚████║███████╗   ██║   ███████║██║ ╚████║██║██║     ██║
  ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝
[/bold cyan]
[dim]          Educational Network Packet Sniffer  v1.0[/dim]
[dim]          For authorized use on your own network only.[/dim]
"""

def parse_args():
    parser = argparse.ArgumentParser(
        prog="sniffer.py",
        description="NetSniff — Educational Network Packet Sniffer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python sniffer.py                         Interactive menu
  sudo python sniffer.py -i eth0                 Sniff on eth0
  sudo python sniffer.py -i eth0 -f tcp          TCP packets only
  sudo python sniffer.py -i eth0 -f udp          UDP packets only
  sudo python sniffer.py -i eth0 -f icmp         ICMP packets only
  sudo python sniffer.py -i eth0 -f http         HTTP traffic (port 80)
  sudo python sniffer.py -i eth0 -f dns          DNS queries
  sudo python sniffer.py -i eth0 --port 443      HTTPS traffic
  sudo python sniffer.py -i eth0 --src 192.168.1.5  From specific IP
  sudo python sniffer.py -i eth0 --dst 8.8.8.8   To specific IP
  sudo python sniffer.py -i eth0 -c 100          Capture 100 packets
  sudo python sniffer.py -i eth0 -o myCapture    Save to file
  sudo python sniffer.py -i eth0 -v              Verbose (full payload)
  sudo python sniffer.py --list-interfaces       List network interfaces
  sudo python sniffer.py --stats                 Show saved session stats
        """
    )

    parser.add_argument("-i", "--interface",
                        help="Network interface to sniff on (e.g. eth0, wlan0)")
    parser.add_argument("-f", "--filter",
                        choices=["tcp", "udp", "icmp", "arp", "dns",
                                 "http", "https", "ftp", "ssh", "all"],
                        default="all",
                        help="Protocol filter (default: all)")
    parser.add_argument("--port", type=int,
                        help="Filter by specific port number")
    parser.add_argument("--src",
                        help="Filter by source IP address")
    parser.add_argument("--dst",
                        help="Filter by destination IP address")
    parser.add_argument("-c", "--count", type=int, default=0,
                        help="Number of packets to capture (0 = unlimited)")
    parser.add_argument("-o", "--output",
                        help="Output filename base (saves .pcap and .json)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose: show full packet payload")
    parser.add_argument("--list-interfaces", action="store_true",
                        help="List all available network interfaces and exit")
    parser.add_argument("--stats", action="store_true",
                        help="Display statistics from the last session")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable colored output")

    return parser.parse_args()


def check_root():
    """Packet sniffing requires root/admin privileges."""
    if os.name == "nt":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            console.print("[bold red][!] Run as Administrator on Windows.[/bold red]")
            sys.exit(1)
    else:
        if os.geteuid() != 0:
            console.print("[bold red][!] Run with sudo on Linux/macOS.[/bold red]")
            console.print("    [dim]Example: sudo python sniffer.py[/dim]")
            sys.exit(1)


def interactive_menu(iface_mgr):
    """Show an interactive setup menu when no CLI args are given."""
    console.print(BANNER)
    console.print(Panel.fit(
        "[bold yellow]Interactive Setup[/bold yellow]\n"
        "No arguments provided — configuring interactively.",
        border_style="yellow"
    ))

    # List interfaces
    interfaces = iface_mgr.list_interfaces()
    console.print("\n[bold cyan]Available Network Interfaces:[/bold cyan]")
    for idx, (name, info) in enumerate(interfaces.items(), 1):
        ip = info.get("ip", "no IP")
        mac = info.get("mac", "??:??:??:??:??:??")
        console.print(f"  [bold white]{idx}.[/bold white] [green]{name}[/green]  "
                      f"[dim]IP: {ip}  MAC: {mac}[/dim]")

    # Interface selection
    iface_names = list(interfaces.keys())
    default_iface = iface_mgr.get_default_interface()
    console.print(f"\n[dim]Default: {default_iface}[/dim]")
    try:
        choice = input("\nSelect interface number (or press Enter for default): ").strip()
        if choice == "":
            interface = default_iface
        else:
            interface = iface_names[int(choice) - 1]
    except (ValueError, IndexError):
        interface = default_iface
    console.print(f"  → Using interface: [bold green]{interface}[/bold green]")

    # Protocol filter
    console.print("\n[bold cyan]Protocol Filter:[/bold cyan]")
    protocols = ["all", "tcp", "udp", "icmp", "arp", "dns", "http", "https", "ftp", "ssh"]
    for idx, p in enumerate(protocols, 1):
        console.print(f"  [bold white]{idx}.[/bold white] {p}")
    try:
        choice = input("\nSelect protocol (or press Enter for 'all'): ").strip()
        proto_filter = protocols[int(choice) - 1] if choice else "all"
    except (ValueError, IndexError):
        proto_filter = "all"
    console.print(f"  → Protocol filter: [bold green]{proto_filter}[/bold green]")

    # Packet count
    try:
        count_str = input("\nPacket count to capture (0 = unlimited, Enter = unlimited): ").strip()
        count = int(count_str) if count_str else 0
    except ValueError:
        count = 0
    console.print(f"  → Packet count: [bold green]{'unlimited' if count == 0 else count}[/bold green]")

    # Verbose
    verbose_str = input("\nVerbose output — show full payload? (y/N): ").strip().lower()
    verbose = verbose_str == "y"

    # Save output
    output_str = input("\nSave to file? Enter base filename (or press Enter to skip): ").strip()
    output = output_str if output_str else None
    if output:
        console.print(f"  → Saving to: [bold green]{output}.pcap[/bold green] and "
                      f"[bold green]{output}.json[/bold green]")

    # Build a namespace that matches argparse output
    class Args:
        pass
    args = Args()
    args.interface   = interface
    args.filter      = proto_filter
    args.port        = None
    args.src         = None
    args.dst         = None
    args.count       = count
    args.output      = output
    args.verbose     = verbose
    args.no_color    = False
    args.list_interfaces = False
    args.stats       = False
    return args


def main():
    args = parse_args()

    # ── List interfaces and exit ──────────────────────────────
    if args.list_interfaces:
        console.print(BANNER)
        iface_mgr = InterfaceManager()
        iface_mgr.print_interfaces()
        sys.exit(0)

    # ── Show stats from last session ──────────────────────────
    if args.stats:
        console.print(BANNER)
        stats = Statistics()
        stats.print_session_summary()
        sys.exit(0)

    # ── Root check ────────────────────────────────────────────
    check_root()

    # ── Interactive menu if no interface given ────────────────
    iface_mgr = InterfaceManager()
    if not args.interface:
        args = interactive_menu(iface_mgr)
    else:
        console.print(BANNER)

    # ── Build filter engine ───────────────────────────────────
    filters = FilterEngine(
        protocol=args.filter,
        port=args.port,
        src_ip=args.src,
        dst_ip=args.dst,
    )

    # ── Statistics tracker ────────────────────────────────────
    stats = Statistics()

    # ── Exporter (optional) ───────────────────────────────────
    exporter = Exporter(args.output) if args.output else None

    # ── Display engine ────────────────────────────────────────
    display = Display(verbose=args.verbose, no_color=args.no_color)

    # ── Capture engine ────────────────────────────────────────
    capture = PacketCapture(
        interface=args.interface,
        filters=filters,
        stats=stats,
        display=display,
        exporter=exporter,
        count=args.count,
    )

    # ── Graceful shutdown ─────────────────────────────────────
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

    # ── Start ─────────────────────────────────────────────────
    display.print_capture_header(args)
    capture.start()


if __name__ == "__main__":
    main()
