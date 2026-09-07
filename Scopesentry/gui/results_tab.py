"""Searchable history of scans and defense findings, pulled from core/db.py."""

from __future__ import annotations

import csv

from PyQt6.QtWidgets import (
    QFileDialog, QGroupBox, QHBoxLayout, QHeaderView, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.db import Database

_SCAN_COLUMNS = ["ID", "Started", "Finished", "AP count"]
_FINDING_COLUMNS = ["Timestamp", "Source", "Type", "ESSID", "Severity", "Details"]


class ResultsTab(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._all_findings: list[dict] = []

        layout = QVBoxLayout(self)

        scans_box = QGroupBox("Scan history")
        scans_layout = QVBoxLayout(scans_box)
        self.scans_table = QTableWidget(0, len(_SCAN_COLUMNS))
        self.scans_table.setHorizontalHeaderLabels(_SCAN_COLUMNS)
        self.scans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.scans_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        scans_layout.addWidget(self.scans_table)
        layout.addWidget(scans_box)

        findings_box = QGroupBox("Findings")
        findings_layout = QVBoxLayout(findings_box)

        controls = QHBoxLayout()
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by ESSID…")
        self.filter_edit.textChanged.connect(self._apply_filter)
        controls.addWidget(self.filter_edit)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(refresh_btn)

        export_btn = QPushButton("Export findings to CSV…")
        export_btn.clicked.connect(self._export_csv)
        controls.addWidget(export_btn)
        findings_layout.addLayout(controls)

        self.findings_table = QTableWidget(0, len(_FINDING_COLUMNS))
        self.findings_table.setHorizontalHeaderLabels(_FINDING_COLUMNS)
        self.findings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.findings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        findings_layout.addWidget(self.findings_table)
        layout.addWidget(findings_box)

        self.refresh()

    def refresh(self):
        scans = self.db.recent_scans()
        self.scans_table.setRowCount(len(scans))
        for row, scan in enumerate(scans):
            values = [str(scan["id"]), scan["started_at"] or "",
                      scan["finished_at"] or "(running)", str(scan["ap_count"])]
            for col, value in enumerate(values):
                self.scans_table.setItem(row, col, QTableWidgetItem(value))

        self._all_findings = self.db.recent_findings()
        self._apply_filter()

    def _apply_filter(self):
        needle = self.filter_edit.text().strip().lower()
        rows = [f for f in self._all_findings if needle in f["essid"].lower()] if needle else self._all_findings
        self.findings_table.setRowCount(len(rows))
        for row, finding in enumerate(rows):
            values = [finding["ts"], finding["source"], finding["finding_type"],
                      finding["essid"], finding["severity"], str(finding["details"])]
            for col, value in enumerate(values):
                self.findings_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export findings", "findings.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ts", "source", "finding_type", "essid", "severity", "details"])
            for finding in self._all_findings:
                writer.writerow([finding["ts"], finding["source"], finding["finding_type"],
                                  finding["essid"], finding["severity"], finding["details"]])