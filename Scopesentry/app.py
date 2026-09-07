"""GUI-Wifite application entry point.

Run:
    python -m app [--iface wlan0mon]

Launches the GUI. The defense monitors and passive scanner need a
monitor-mode interface and (for the deauth monitor) tshark; the rest of
the UI runs without special privileges.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GUI-Wifite defensive WiFi monitor")
    parser.add_argument("--iface", default="wlan0mon",
                         help="monitor-mode interface for passive monitoring")
    args = parser.parse_args(argv)

    # Imported here so --help works without PyQt6 installed.
    from PyQt6.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication(sys.argv[:1])
    window = MainWindow(mon_iface=args.iface)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
