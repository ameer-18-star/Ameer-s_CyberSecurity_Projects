"""Generic QThread runner for short, non-interactive system commands.

This is deliberately a thin, generic subprocess wrapper — it builds nothing
tool-specific. Everything in this project that uses it points it only at
observation/management commands (iw, airmon-ng, tshark in read-only capture
mode). Nothing in this codebase constructs a reaver, aireplay-ng,
hcxdumptool, bully, or hashcat command.
"""

from __future__ import annotations

import subprocess

from PyQt6.QtCore import QThread, pyqtSignal


class CommandRunner(QThread):
    log_line = pyqtSignal(str)
    finished_ok = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, cmd: list[str], parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self._proc: subprocess.Popen | None = None
        self._stop_requested = False

    def run(self):
        try:
            self._proc = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except FileNotFoundError:
            self.error.emit(f"Tool not found: {self.cmd[0]} — is it installed?")
            return
        except OSError as exc:
            self.error.emit(str(exc))
            return

        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            if self._stop_requested:
                break
            self.log_line.emit(line.rstrip())
        self._proc.wait()
        self.finished_ok.emit(self._proc.returncode)

    def stop(self):
        self._stop_requested = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()