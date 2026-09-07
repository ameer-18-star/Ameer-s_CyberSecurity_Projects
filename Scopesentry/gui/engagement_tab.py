"""Load an engagement manifest and show whether it's currently active.

This is informational bookkeeping, not a gate on anything in this app —
there's no attack engine here for it to gate. Its purpose is to make the
authorized scope and time window visible and to put a record of when it
was loaded into the evidence log, in case that matters for whatever process
you're running this alongside.
"""

from __future__ import annotations

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog, QGroupBox, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QVBoxLayout, QWidget,
)

from core.engagement import EngagementManifest, InvalidManifest
from core.evidence_log import EvidenceLog


class EngagementTab(QWidget):
    log_line = pyqtSignal(str)
    manifest_loaded = pyqtSignal(object)   # EngagementManifest

    def __init__(self, evidence: EvidenceLog, parent=None):
        super().__init__(parent)
        self.evidence = evidence
        self.manifest: EngagementManifest | None = None

        layout = QVBoxLayout(self)

        load_row = QHBoxLayout()
        load_btn = QPushButton("Load manifest…")
        load_btn.clicked.connect(self._load_manifest)
        load_row.addWidget(load_btn)
        load_row.addStretch(1)
        layout.addLayout(load_row)

        self.status_label = QLabel("No manifest loaded.")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        details_box = QGroupBox("Engagement details")
        details_layout = QVBoxLayout(details_box)
        self.details_label = QLabel("—")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)
        layout.addWidget(details_box)

        bssid_box = QGroupBox("Authorized BSSIDs")
        bssid_layout = QVBoxLayout(bssid_box)
        self.bssid_list = QListWidget()
        bssid_layout.addWidget(self.bssid_list)
        layout.addWidget(bssid_box)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start(30_000)  # re-check window every 30s

    def _load_manifest(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load engagement manifest", "", "JSON (*.json)")
        if not path:
            return
        try:
            manifest = EngagementManifest.load(path)
        except (InvalidManifest, OSError, ValueError) as exc:
            self.status_label.setText(f"Failed to load manifest: {exc}")
            self.log_line.emit(f"manifest load failed: {exc}")
            return

        self.manifest = manifest
        self.evidence.record(
            "manifest_loaded",
            engagement_id=manifest.engagement_id,
            client=manifest.client,
            bssid_count=len(manifest.authorized_bssids),
        )
        self.log_line.emit(f"loaded manifest {manifest.engagement_id} for {manifest.client}")

        self.details_label.setText(
            f"Engagement ID: {manifest.engagement_id}\n"
            f"Client: {manifest.client}\n"
            f"Tester: {manifest.tester}\n"
            f"Authorized by: {manifest.authorized_by}\n"
            f"Window: {manifest.window_start} → {manifest.window_end}"
        )
        self.bssid_list.clear()
        self.bssid_list.addItems(sorted(manifest.authorized_bssids))

        self._refresh_status()
        self.manifest_loaded.emit(manifest)

    def _refresh_status(self):
        if self.manifest is None:
            self.status_label.setText("No manifest loaded.")
            return
        if self.manifest.is_within_window():
            self.status_label.setText(f"ACTIVE — within window for {self.manifest.engagement_id}")
            self.status_label.setStyleSheet("font-weight: bold; color: #4caf50;")
        else:
            self.status_label.setText(f"INACTIVE — outside window for {self.manifest.engagement_id}")
            self.status_label.setStyleSheet("font-weight: bold; color: #e57373;")