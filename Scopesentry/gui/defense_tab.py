"""Baseline manager + the three defense checks (rogue-AP, hardening, deauth flood).

Everything here is read-only/passive: rogue-AP and hardening checks compare
the latest passive scan against a baseline you define for your own
networks, and the deauth monitor only listens. Nothing here transmits.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView, QDoubleSpinBox, QGroupBox, QHBoxLayout, QHeaderView,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.db import Database
from core.defense.deauth_monitor import DeauthMonitor
from core.defense.hardening_audit import audit as hardening_audit
from core.defense.rogue_ap_monitor import RogueAPMonitor
from core.evidence_log import EvidenceLog
from core.models import APRecord, BaselineAP

_BASELINE_COLUMNS = ["ESSID", "BSSID", "Expected encryption", "Expected channel"]
_ALERT_COLUMNS = ["Source", "Type/Issue", "ESSID", "Severity", "Detail"]


class DefenseTab(QWidget):
    log_line = pyqtSignal(str)

    def __init__(self, db: Database, evidence: EvidenceLog, parent=None):
        super().__init__(parent)
        self.db = db
        self.evidence = evidence
        self.mon_iface: str | None = None
        self._latest_aps: list[APRecord] = []
        self._deauth_monitor: DeauthMonitor | None = None

        layout = QVBoxLayout(self)

        # --- baseline manager -------------------------------------------------------
        baseline_box = QGroupBox("Baseline (your own networks)")
        baseline_layout = QVBoxLayout(baseline_box)

        self.baseline_table = QTableWidget(0, len(_BASELINE_COLUMNS))
        self.baseline_table.setHorizontalHeaderLabels(_BASELINE_COLUMNS)
        self.baseline_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        baseline_layout.addWidget(self.baseline_table)

        baseline_controls = QHBoxLayout()
        add_row_btn = QPushButton("Add row")
        add_row_btn.clicked.connect(self._add_baseline_row)
        remove_row_btn = QPushButton("Remove selected")
        remove_row_btn.clicked.connect(self._remove_baseline_row)
        baseline_controls.addWidget(add_row_btn)
        baseline_controls.addWidget(remove_row_btn)
        baseline_controls.addStretch(1)
        baseline_layout.addLayout(baseline_controls)

        layout.addWidget(baseline_box)

        # --- checks -------------------------------------------------------------------
        checks_row = QHBoxLayout()
        run_checks_btn = QPushButton("Run rogue-AP + hardening checks now")
        run_checks_btn.clicked.connect(self._run_checks)
        checks_row.addWidget(run_checks_btn)
        checks_row.addStretch(1)
        layout.addLayout(checks_row)

        # --- deauth monitor -------------------------------------------------------------
        deauth_box = QGroupBox("Deauth-flood monitor (passive — listens only)")
        deauth_layout = QHBoxLayout(deauth_box)

        deauth_layout.addWidget(_label("Threshold:"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 1000)
        self.threshold_spin.setValue(15)
        deauth_layout.addWidget(self.threshold_spin)

        deauth_layout.addWidget(_label("Window (s):"))
        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(1.0, 300.0)
        self.window_spin.setValue(10.0)
        deauth_layout.addWidget(self.window_spin)

        self.start_deauth_btn = QPushButton("Start monitoring")
        self.start_deauth_btn.clicked.connect(self._start_deauth_monitor)
        self.stop_deauth_btn = QPushButton("Stop")
        self.stop_deauth_btn.clicked.connect(self._stop_deauth_monitor)
        self.stop_deauth_btn.setEnabled(False)
        deauth_layout.addWidget(self.start_deauth_btn)
        deauth_layout.addWidget(self.stop_deauth_btn)
        deauth_layout.addStretch(1)

        layout.addWidget(deauth_box)

        # --- alerts -------------------------------------------------------------------
        alerts_box = QGroupBox("Findings / alerts")
        alerts_layout = QVBoxLayout(alerts_box)
        self.alerts_table = QTableWidget(0, len(_ALERT_COLUMNS))
        self.alerts_table.setHorizontalHeaderLabels(_ALERT_COLUMNS)
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.alerts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        alerts_layout.addWidget(self.alerts_table)
        layout.addWidget(alerts_box)

    # ---- wiring from MainWindow --------------------------------------------------

    def set_mon_iface(self, iface: str):
        self.mon_iface = iface
        self.log_line.emit(f"defense tab will use {iface} for the deauth monitor")

    def update_scan(self, aps: list[APRecord]):
        self._latest_aps = aps

    def apply_settings(self, threshold: int, window_seconds: float):
        self.threshold_spin.setValue(threshold)
        self.window_spin.setValue(window_seconds)

    # ---- baseline table ----------------------------------------------------------

    def _add_baseline_row(self):
        row = self.baseline_table.rowCount()
        self.baseline_table.insertRow(row)
        defaults = ["", "", "WPA2", ""]
        for col, value in enumerate(defaults):
            self.baseline_table.setItem(row, col, QTableWidgetItem(value))

    def _remove_baseline_row(self):
        for index in sorted({i.row() for i in self.baseline_table.selectedIndexes()}, reverse=True):
            self.baseline_table.removeRow(index)

    def _read_baseline(self) -> list[BaselineAP]:
        baseline = []
        for row in range(self.baseline_table.rowCount()):
            def cell(col):
                item = self.baseline_table.item(row, col)
                return item.text().strip() if item else ""

            essid, bssid, enc, channel = cell(0), cell(1), cell(2), cell(3)
            if essid and bssid:
                baseline.append(BaselineAP(
                    essid=essid, bssid=bssid,
                    expected_encryption=enc or "WPA2",
                    expected_channel=channel,
                ))
        return baseline

    # ---- checks --------------------------------------------------------------------

    def _run_checks(self):
        baseline = self._read_baseline()
        if not baseline:
            self.log_line.emit("baseline is empty — add your own networks first")
            return
        if not self._latest_aps:
            self.log_line.emit("no scan data yet — start a scan on the Dashboard tab first")
            return

        baseline_essids = {b.essid for b in baseline}
        rogue_alerts = RogueAPMonitor(baseline).check(self._latest_aps)
        hardening_findings = hardening_audit(self._latest_aps, baseline_essids)

        for alert in rogue_alerts:
            self._record_and_show("rogue_ap", alert.type.value, alert.essid,
                                   alert.to_finding().severity, alert.detail)
        for finding in hardening_findings:
            self._record_and_show("hardening", finding.issue, finding.essid,
                                   finding.to_finding().severity,
                                   {"recommendation": finding.recommendation})

        self.log_line.emit(
            f"checks complete: {len(rogue_alerts)} rogue-AP alert(s), "
            f"{len(hardening_findings)} hardening finding(s)"
        )

    def _record_and_show(self, source: str, label: str, essid: str, severity: str, detail: dict):
        self.db.record_finding(_make_finding(source, label, essid, severity, detail))
        self.evidence.record("finding", source=source, label=label, essid=essid,
                              severity=severity, detail=detail)
        row = self.alerts_table.rowCount()
        self.alerts_table.insertRow(row)
        for col, value in enumerate([source, label, essid, severity, str(detail)]):
            self.alerts_table.setItem(row, col, QTableWidgetItem(value))

    # ---- deauth monitor --------------------------------------------------------------

    def _start_deauth_monitor(self):
        if not self.mon_iface:
            self.log_line.emit("no monitor interface — start monitor mode on the Dashboard tab first")
            return
        baseline_bssids = {b.bssid for b in self._read_baseline()}
        if not baseline_bssids:
            self.log_line.emit("baseline is empty — add your own networks' BSSIDs first")
            return

        self._deauth_monitor = DeauthMonitor(
            self.mon_iface, baseline_bssids,
            threshold=self.threshold_spin.value(),
            window_seconds=self.window_spin.value(),
        )
        self._deauth_monitor.flood_detected.connect(self._on_flood_detected)
        self._deauth_monitor.status.connect(self.log_line.emit)
        self._deauth_monitor.error.connect(lambda msg: self.log_line.emit(f"deauth monitor error: {msg}"))
        self._deauth_monitor.start()
        self.start_deauth_btn.setEnabled(False)
        self.stop_deauth_btn.setEnabled(True)

    def _stop_deauth_monitor(self):
        if self._deauth_monitor:
            self._deauth_monitor.stop()
            self._deauth_monitor.wait(2000)
            self._deauth_monitor = None
        self.start_deauth_btn.setEnabled(True)
        self.stop_deauth_btn.setEnabled(False)
        self.log_line.emit("deauth monitor stopped")

    def _on_flood_detected(self, bssid: str, count: int):
        detail = {"frame_count": count, "window_seconds": self.window_spin.value()}
        self._record_and_show("deauth_flood", "deauth_or_disassoc_flood", bssid, "critical", detail)
        self.log_line.emit(f"DEAUTH FLOOD on {bssid}: {count} frames — possible attack in progress")


def _label(text: str):
    from PyQt6.QtWidgets import QLabel
    return QLabel(text)


def _make_finding(source: str, finding_type: str, essid: str, severity: str, details: dict):
    from core.models import Finding
    return Finding(source=source, finding_type=finding_type, essid=essid,
                   severity=severity, details=details)