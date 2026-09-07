"""Interface picker, monitor-mode toggle, and the live passive scan table.

Everything here is observation/management: listing interfaces, toggling
monitor mode via airmon-ng, and running airodump-ng with no --bssid/-c lock
tied to any injection tool. There is no attack action anywhere on this tab.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.interface_manager import InterfaceManager
from core.models import APRecord
from core.scanner import ScannerThread


class DashboardTab(QWidget):
    log_line = pyqtSignal(str)
    monitor_ready = pyqtSignal(str)     # mon_iface, once monitor mode is presumed up
    aps_updated = pyqtSignal(list)      # list[APRecord], forwarded for other tabs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mon_iface: str | None = None
        self._monitor_runner = None
        self._scanner: ScannerThread | None = None
        self._latest_aps: list[APRecord] = []

        layout = QVBoxLayout(self)

        # --- interface / monitor mode -------------------------------------------------
        iface_box = QGroupBox("Interface")
        iface_layout = QHBoxLayout(iface_box)

        self.iface_combo = QComboBox()
        self.iface_combo.setEditable(True)
        iface_layout.addWidget(self.iface_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_interfaces)
        iface_layout.addWidget(refresh_btn)

        start_mon_btn = QPushButton("Start monitor mode")
        start_mon_btn.clicked.connect(self._start_monitor_mode)
        iface_layout.addWidget(start_mon_btn)

        stop_mon_btn = QPushButton("Stop monitor mode")
        stop_mon_btn.clicked.connect(self._stop_monitor_mode)
        iface_layout.addWidget(stop_mon_btn)

        layout.addWidget(iface_box)

        self.status_label = QLabel("Monitor mode: not started")
        layout.addWidget(self.status_label)

        # --- passive scan ---------------------------------------------------------
        scan_box = QGroupBox("Passive scan")
        scan_layout = QVBoxLayout(scan_box)

        scan_controls = QHBoxLayout()
        self.start_scan_btn = QPushButton("Start scan")
        self.start_scan_btn.clicked.connect(self._start_scan)
        self.stop_scan_btn = QPushButton("Stop scan")
        self.stop_scan_btn.clicked.connect(self._stop_scan)
        self.stop_scan_btn.setEnabled(False)
        scan_controls.addWidget(self.start_scan_btn)
        scan_controls.addWidget(self.stop_scan_btn)
        scan_controls.addStretch(1)
        self.ap_count_label = QLabel("APs seen: 0")
        scan_controls.addWidget(self.ap_count_label)
        scan_layout.addLayout(scan_controls)

        self.ap_table = QTableWidget(0, 6)
        self.ap_table.setHorizontalHeaderLabels(
            ["ESSID", "BSSID", "Channel", "Encryption", "Signal", "Clients"]
        )
        self.ap_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ap_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        scan_layout.addWidget(self.ap_table)

        layout.addWidget(scan_box)

        self._refresh_interfaces()

    # ---- interface management -------------------------------------------------

    def _refresh_interfaces(self):
        ifaces = InterfaceManager.list_interfaces()
        self.iface_combo.clear()
        self.iface_combo.addItems(ifaces)
        self.log_line.emit(f"found interfaces: {ifaces}" if ifaces else "no interfaces found (is iw installed?)")

    def _start_monitor_mode(self):
        iface = self.iface_combo.currentText().strip()
        if not iface:
            self.log_line.emit("no interface selected")
            return
        self._monitor_runner = InterfaceManager.start_monitor_mode(iface)
        self._monitor_runner.log_line.connect(lambda line: self.log_line.emit(line))
        self._monitor_runner.error.connect(lambda msg: self.log_line.emit(f"error: {msg}"))

        def on_finished(code: int):
            # airmon-ng commonly renames the interface to "<iface>mon"; this is a
            # reasonable default guess, editable below if your driver differs.
            guessed = iface if iface.endswith("mon") else f"{iface}mon"
            self.mon_iface = guessed
            self.iface_combo.setEditText(guessed)
            self.status_label.setText(f"Monitor mode: started on {guessed} (exit code {code})")
            self.monitor_ready.emit(guessed)
            self.log_line.emit(f"monitor mode presumed up on {guessed} — verify with 'iw dev'")

        self._monitor_runner.finished_ok.connect(on_finished)
        self._monitor_runner.start()
        self.log_line.emit(f"starting monitor mode on {iface}…")

    def _stop_monitor_mode(self):
        iface = self.mon_iface or self.iface_combo.currentText().strip()
        if not iface:
            return
        runner = InterfaceManager.stop_monitor_mode(iface)
        runner.log_line.connect(lambda line: self.log_line.emit(line))
        runner.finished_ok.connect(
            lambda code: self.status_label.setText(f"Monitor mode: stopped on {iface}")
        )
        runner.start()
        self._monitor_runner = runner
        self.log_line.emit(f"stopping monitor mode on {iface}…")

    # ---- passive scan ----------------------------------------------------------

    def _start_scan(self):
        iface = self.mon_iface or self.iface_combo.currentText().strip()
        if not iface:
            self.log_line.emit("no interface to scan with — start monitor mode first")
            return
        self._scanner = ScannerThread(iface)
        self._scanner.aps_updated.connect(self._on_aps_updated)
        self._scanner.error.connect(lambda msg: self.log_line.emit(f"scanner error: {msg}"))
        self._scanner.start()
        self.start_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        self.log_line.emit(f"passive scan started on {iface}")

    def _stop_scan(self):
        if self._scanner:
            self._scanner.stop()
            self._scanner.wait(2000)
            self._scanner = None
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.log_line.emit("passive scan stopped")

    def _on_aps_updated(self, aps: list[APRecord]):
        self._latest_aps = aps
        self.ap_count_label.setText(f"APs seen: {len(aps)}")
        self.ap_table.setRowCount(len(aps))
        for row, ap in enumerate(sorted(aps, key=lambda a: a.essid.lower())):
            values = [ap.essid, ap.bssid, ap.channel, ap.encryption,
                      str(ap.signal) if ap.signal is not None else "—", str(ap.clients)]
            for col, value in enumerate(values):
                self.ap_table.setItem(row, col, QTableWidgetItem(value))
        self.aps_updated.emit(aps)