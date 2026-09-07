"""Raw streaming console output from whichever monitor/worker is active.

Every other tab's worker threads (CommandRunner, ScannerThread,
DeauthMonitor, ...) connect their log_line/status/error signals here via
MainWindow, so this is the one place to watch everything happening.
"""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class LogsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.console = QPlainTextEdit(readOnly=True)
        self.console.setMaximumBlockCount(5000)
        self.console.setStyleSheet("font-family: monospace; font-size: 12px;")
        layout.addWidget(self.console)

        controls = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.console.clear)
        controls.addStretch(1)
        controls.addWidget(clear_btn)
        layout.addLayout(controls)

    def append_line(self, text: str, source: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{ts}]" + (f" [{source}]" if source else "")
        self.console.appendPlainText(f"{prefix} {text}")