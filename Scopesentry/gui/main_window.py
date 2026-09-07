"""Main window: owns the shared Database/EvidenceLog and wires tabs together.

Cross-tab wiring, all of it observation/process plumbing:
- Dashboard's monitor_ready -> Defense's mon_iface (so the deauth monitor
  knows which interface to listen on)
- Dashboard's aps_updated  -> Defense's latest scan snapshot (for the
  rogue-AP/hardening checks) and a scans-table row in the database
- Every tab's log_line     -> the shared Logs console
- Settings changes         -> Defense's threshold/window + theme
"""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from core.db import Database
from core.evidence_log import EvidenceLog
from gui.dashboard_tab import DashboardTab
from gui.defense_tab import DefenseTab
from gui.engagement_tab import EngagementTab
from gui.evidence_tab import EvidenceTab
from gui.logs_tab import LogsTab
from gui.results_tab import ResultsTab
from gui.settings_tab import SettingsTab, DEFAULT_SETTINGS


class MainWindow(QMainWindow):
    def __init__(self, mon_iface: str = "wlan0mon",
                 db_path: str = DEFAULT_SETTINGS["db_path"],
                 evidence_path: str = DEFAULT_SETTINGS["evidence_path"],
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("ScopeSentry")
        self.resize(1150, 760)

        self.db = Database(db_path)
        self.evidence = EvidenceLog(evidence_path)

        self.dashboard_tab = DashboardTab()
        self.engagement_tab = EngagementTab(self.evidence)
        self.defense_tab = DefenseTab(self.db, self.evidence)
        self.evidence_tab = EvidenceTab(self.evidence)
        self.results_tab = ResultsTab(self.db)
        self.logs_tab = LogsTab()
        self.settings_tab = SettingsTab(initial={
            "db_path": db_path, "evidence_path": evidence_path,
        })

        if mon_iface:
            self.defense_tab.set_mon_iface(mon_iface)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.engagement_tab, "Engagement")
        self.tabs.addTab(self.defense_tab, "Defense")
        self.tabs.addTab(self.evidence_tab, "Evidence")
        self.tabs.addTab(self.results_tab, "Results")
        self.tabs.addTab(self.logs_tab, "Logs")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.setCentralWidget(self.tabs)

        self._wire_signals()

    def _wire_signals(self):
        # Every tab's chatter ends up in one console.
        self.dashboard_tab.log_line.connect(lambda line: self.logs_tab.append_line(line, "dashboard"))
        self.engagement_tab.log_line.connect(lambda line: self.logs_tab.append_line(line, "engagement"))
        self.defense_tab.log_line.connect(lambda line: self.logs_tab.append_line(line, "defense"))

        # Dashboard discovers the monitor interface -> Defense uses it for the deauth monitor.
        self.dashboard_tab.monitor_ready.connect(self.defense_tab.set_mon_iface)

        # Dashboard's live scan -> Defense's latest snapshot for on-demand checks,
        # and a row in the scan-history table.
        self.dashboard_tab.aps_updated.connect(self.defense_tab.update_scan)
        self.dashboard_tab.aps_updated.connect(self._record_scan)

        # Settings -> Defense thresholds. (DB/evidence paths take effect on restart;
        # swapping live storage backends mid-session isn't handled here.)
        self.settings_tab.settings_changed.connect(
            lambda values: self.defense_tab.apply_settings(
                values["deauth_threshold"], values["deauth_window_seconds"]
            )
        )

        # Refresh the read-only tabs whenever something might have changed.
        self.defense_tab.log_line.connect(lambda _line: self.results_tab.refresh())
        self.defense_tab.log_line.connect(lambda _line: self.evidence_tab.refresh())
        self.engagement_tab.log_line.connect(lambda _line: self.evidence_tab.refresh())

    def _record_scan(self, aps: list):
        scan_id = self.db.start_scan()
        self.db.finish_scan(scan_id, ap_count=len(aps))
        self.results_tab.refresh()


def run(mon_iface: str = "wlan0mon") -> int:
    import sys
    app = QApplication(sys.argv[:1])
    window = MainWindow(mon_iface=mon_iface)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())