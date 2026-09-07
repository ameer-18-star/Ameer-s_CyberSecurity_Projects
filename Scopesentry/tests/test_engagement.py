from datetime import datetime, timedelta

import pytest

from core.engagement import EngagementManifest, InvalidManifest


def make_manifest_dict(**overrides):
    base = {
        "engagement_id": "ACME-2026-06",
        "client": "Acme Corp",
        "tester": "Tester Name",
        "authorized_by": "Jane Doe, CISO",
        "window_start": "2026-06-24T09:00:00",
        "window_end": "2026-06-26T18:00:00",
        "authorized_targets": [
            {"bssid": "AA:BB:CC:11:22:33", "essid": "Acme-Corp-WiFi"},
            {"bssid": "AA:BB:CC:44:55:66", "essid": "Acme-Guest"},
        ],
    }
    base.update(overrides)
    return base


def test_loads_valid_manifest():
    m = EngagementManifest.from_dict(make_manifest_dict())
    assert m.engagement_id == "ACME-2026-06"
    assert "AA:BB:CC:11:22:33" in m.authorized_bssids


def test_bssid_in_scope_case_insensitive():
    m = EngagementManifest.from_dict(make_manifest_dict())
    assert m.is_in_scope("aa:bb:cc:11:22:33")
    assert m.is_in_scope("AA:BB:CC:11:22:33")


def test_bssid_out_of_scope():
    m = EngagementManifest.from_dict(make_manifest_dict())
    assert not m.is_in_scope("DE:AD:BE:EF:00:01")


def test_within_window():
    m = EngagementManifest.from_dict(make_manifest_dict())
    inside = datetime(2026, 6, 25, 12, 0, 0)
    assert m.is_within_window(inside)


def test_outside_window_before_start():
    m = EngagementManifest.from_dict(make_manifest_dict())
    before = datetime(2026, 6, 20, 0, 0, 0)
    assert not m.is_within_window(before)


def test_outside_window_after_end():
    m = EngagementManifest.from_dict(make_manifest_dict())
    after = datetime(2026, 7, 1, 0, 0, 0)
    assert not m.is_within_window(after)


def test_authorize_requires_both_conditions():
    m = EngagementManifest.from_dict(make_manifest_dict())
    in_window = datetime(2026, 6, 25, 12, 0, 0)
    out_window = datetime(2026, 7, 1, 0, 0, 0)

    assert m.authorize("AA:BB:CC:11:22:33", now=in_window) is True
    assert m.authorize("AA:BB:CC:11:22:33", now=out_window) is False
    assert m.authorize("DE:AD:BE:EF:00:01", now=in_window) is False


def test_reason_if_blocked_out_of_scope():
    m = EngagementManifest.from_dict(make_manifest_dict())
    reason = m.reason_if_blocked("DE:AD:BE:EF:00:01", now=datetime(2026, 6, 25))
    assert reason is not None
    assert "not in the authorized_targets" in reason


def test_reason_if_blocked_out_of_window():
    m = EngagementManifest.from_dict(make_manifest_dict())
    reason = m.reason_if_blocked("AA:BB:CC:11:22:33", now=datetime(2026, 7, 1))
    assert reason is not None
    assert "outside the engagement window" in reason


def test_reason_if_blocked_returns_none_when_authorized():
    m = EngagementManifest.from_dict(make_manifest_dict())
    reason = m.reason_if_blocked("AA:BB:CC:11:22:33", now=datetime(2026, 6, 25))
    assert reason is None


def test_rejects_empty_target_list():
    with pytest.raises(InvalidManifest):
        EngagementManifest.from_dict(make_manifest_dict(authorized_targets=[]))


def test_rejects_inverted_window():
    with pytest.raises(InvalidManifest):
        EngagementManifest.from_dict(make_manifest_dict(
            window_start="2026-06-26T18:00:00",
            window_end="2026-06-24T09:00:00",
        ))


def test_rejects_missing_field():
    data = make_manifest_dict()
    del data["client"]
    with pytest.raises(InvalidManifest):
        EngagementManifest.from_dict(data)


def test_rejects_malformed_bssid():
    with pytest.raises(InvalidManifest):
        EngagementManifest.from_dict(make_manifest_dict(
            authorized_targets=[{"bssid": "not-a-mac", "essid": "X"}]
        ))


def test_rejects_bad_date_format():
    with pytest.raises(InvalidManifest):
        EngagementManifest.from_dict(make_manifest_dict(window_start="not-a-date"))


def test_load_from_file(tmp_path):
    import json
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(make_manifest_dict()))
    m = EngagementManifest.load(p)
    assert m.engagement_id == "ACME-2026-06"
