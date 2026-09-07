"""View the hash-chained evidence log and verify it hasn't been tampered with."""

from __future__ import annotations

import json

from PyQt6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.evidence_log import EvidenceLog

_COLUMNS = ["Timestamp", "Event", "Fields", "Entry hash (short)"]


class EvidenceTab(QWidget):
    def __init__(self, evidence: EvidenceLog, parent=None):
        super().__init__(parent)
        self.evidence = evidence

        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        verify_btn = QPushButton("Verify chain")
        verify_btn.clicked.connect(self._verify_chain)
        controls.addWidget(refresh_btn)
        controls.addWidget(verify_btn)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.verify_label = QLabel("Chain not yet verified.")
        layout.addWidget(self.verify_label)

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        entries = self.evidence.read_all()
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            fields = {k: v for k, v in entry.items()
                      if k not in ("ts", "event", "prev_hash", "entry_hash")}
            values = [
                entry.get("ts", ""),
                entry.get("event", ""),
                json.dumps(fields, sort_keys=True),
                entry.get("entry_hash", "")[:12],
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def _verify_chain(self):
        ok, message = self.evidence.verify_chain()
        color = "#4caf50" if ok else "#e57373"
        prefix = "OK" if ok else "FAILED"
        self.verify_label.setText(f"{prefix}: {message}")
        self.verify_label.setStyleSheet(f"font-weight: bold; color: {color};")