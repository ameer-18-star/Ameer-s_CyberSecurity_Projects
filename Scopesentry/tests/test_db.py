from core.db import Database
from core.models import Finding


def test_start_and_finish_scan(tmp_path):
    db = Database(tmp_path / "test.db")
    scan_id = db.start_scan()
    db.finish_scan(scan_id, ap_count=5)
    scans = db.recent_scans()
    assert scans[0]["id"] == scan_id
    assert scans[0]["ap_count"] == 5
    assert scans[0]["finished_at"] is not None


def test_scan_in_progress_has_no_finished_at(tmp_path):
    db = Database(tmp_path / "test.db")
    db.start_scan()
    scans = db.recent_scans()
    assert scans[0]["finished_at"] is None


def test_record_and_read_finding(tmp_path):
    db = Database(tmp_path / "test.db")
    finding = Finding(
        source="hardening", finding_type="weak_encryption",
        essid="Acme-Corp-WiFi", severity="critical",
        details={"seen": "WEP"},
    )
    db.record_finding(finding)
    findings = db.recent_findings()
    assert len(findings) == 1
    assert findings[0]["essid"] == "Acme-Corp-WiFi"
    assert findings[0]["details"]["seen"] == "WEP"


def test_recent_findings_respects_limit(tmp_path):
    db = Database(tmp_path / "test.db")
    for i in range(5):
        db.record_finding(Finding(
            source="rogue_ap", finding_type="bssid_mismatch",
            essid=f"SSID-{i}", severity="info", details={},
        ))
    assert len(db.recent_findings(limit=3)) == 3


def test_findings_ordered_most_recent_first(tmp_path):
    db = Database(tmp_path / "test.db")
    db.record_finding(Finding(source="rogue_ap", finding_type="x", essid="first", severity="info", details={}))
    db.record_finding(Finding(source="rogue_ap", finding_type="x", essid="second", severity="info", details={}))
    findings = db.recent_findings()
    assert findings[0]["essid"] == "second"
    assert findings[1]["essid"] == "first"


def test_schema_is_idempotent(tmp_path):
    path = tmp_path / "test.db"
    Database(path)
    Database(path)  # reopening must not fail re-creating tables