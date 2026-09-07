"""SQLite persistence for scan history and defense findings.

There is no "cracked credentials" table here, deliberately — this project
has no crack engine. What gets persisted is recon history and the output of
the three defense modules, for the Results tab and for trend-watching over
time (e.g. "has this rogue-AP alert fired before").
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from core.models import Finding

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    ap_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    source TEXT NOT NULL,
    finding_type TEXT NOT NULL,
    essid TEXT NOT NULL,
    severity TEXT NOT NULL,
    details_json TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def start_scan(self) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO scans (started_at, ap_count) VALUES (?, 0)",
                (datetime.now().isoformat(),),
            )
            return cur.lastrowid

    def finish_scan(self, scan_id: int, ap_count: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE scans SET finished_at = ?, ap_count = ? WHERE id = ?",
                (datetime.now().isoformat(), ap_count, scan_id),
            )

    def record_finding(self, finding: Finding) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO findings (ts, source, finding_type, essid, severity, details_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now().isoformat(),
                    finding.source,
                    finding.finding_type,
                    finding.essid,
                    finding.severity,
                    json.dumps(finding.details),
                ),
            )
            return cur.lastrowid

    def recent_findings(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT ts, source, finding_type, essid, severity, details_json "
                "FROM findings ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "ts": r[0], "source": r[1], "finding_type": r[2],
                "essid": r[3], "severity": r[4], "details": json.loads(r[5]),
            }
            for r in rows
        ]

    def recent_scans(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, started_at, finished_at, ap_count "
                "FROM scans ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"id": r[0], "started_at": r[1], "finished_at": r[2], "ap_count": r[3]}
            for r in rows
        ]