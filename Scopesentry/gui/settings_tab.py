"""Tunables: deauth-flood threshold/window, storage paths, theme.

Changes apply immediately (no separate Save step) and are broadcast via
settings_changed so MainWindow can push the new values into DefenseTab.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QDoubleSpinBox, QFormLayout, QLineEdit, QSpinBox, QWidget,
)

DEFAULT_SETTINGS = {
    "deauth_threshold": 15,
    "deauth_window_seconds": 10.0,
    "db_path": "scopesentry.db",
    "evidence_path": "evidence.jsonl",
    "dark_theme": True,
}


class SettingsTab(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, initial: dict | None = None, parent=None):
        super().__init__(parent)
        self.values = {**DEFAULT_SETTINGS, **(initial or {})}

        form = QFormLayout(self)

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 1000)
        self.threshold_spin.setValue(self.values["deauth_threshold"])
        self.threshold_spin.valueChanged.connect(self._emit_changed)
        form.addRow("Deauth flood threshold (frames/window):", self.threshold_spin)

        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(1.0, 300.0)
        self.window_spin.setSingleStep(1.0)
        self.window_spin.setValue(self.values["deauth_window_seconds"])
        self.window_spin.valueChanged.connect(self._emit_changed)
        form.addRow("Deauth flood window (seconds):", self.window_spin)

        self.db_path_edit = QLineEdit(self.values["db_path"])
        self.db_path_edit.editingFinished.connect(self._emit_changed)
        form.addRow("Database path:", self.db_path_edit)

        self.evidence_path_edit = QLineEdit(self.values["evidence_path"])
        self.evidence_path_edit.editingFinished.connect(self._emit_changed)
        form.addRow("Evidence log path:", self.evidence_path_edit)

        self.dark_theme_check = QCheckBox("Dark theme")
        self.dark_theme_check.setChecked(self.values["dark_theme"])
        self.dark_theme_check.toggled.connect(self._emit_changed)
        form.addRow(self.dark_theme_check)

    def _emit_changed(self):
        self.values = {
            "deauth_threshold": self.threshold_spin.value(),
            "deauth_window_seconds": self.window_spin.value(),
            "db_path": self.db_path_edit.text().strip() or DEFAULT_SETTINGS["db_path"],
            "evidence_path": self.evidence_path_edit.text().strip() or DEFAULT_SETTINGS["evidence_path"],
            "dark_theme": self.dark_theme_check.isChecked(),
        }
        self.settings_changed.emit(dict(self.values))