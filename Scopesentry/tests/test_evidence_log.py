import json

from core.evidence_log import EvidenceLog, GENESIS_HASH


def test_first_entry_chains_from_genesis(tmp_path):
    log = EvidenceLog(tmp_path / "evidence.jsonl")
    log.record("scope_pass", bssid="AA:BB:CC:11:22:33")
    entries = log.read_all()
    assert entries[0]["prev_hash"] == GENESIS_HASH


def test_chain_links_correctly(tmp_path):
    log = EvidenceLog(tmp_path / "evidence.jsonl")
    h1 = log.record("scope_pass", bssid="AA:BB:CC:11:22:33")
    entries = log.read_all()
    assert entries[0]["entry_hash"] == h1

    log.record("scope_block", bssid="DE:AD:BE:EF:00:01")
    entries = log.read_all()
    assert entries[1]["prev_hash"] == h1


def test_verify_chain_passes_on_untouched_log(tmp_path):
    log = EvidenceLog(tmp_path / "evidence.jsonl")
    log.record("a")
    log.record("b")
    log.record("c")
    ok, _ = log.verify_chain()
    assert ok is True


def test_verify_chain_detects_field_tampering(tmp_path):
    path = tmp_path / "evidence.jsonl"
    log = EvidenceLog(path)
    log.record("scope_pass", bssid="AA:BB:CC:11:22:33")

    lines = path.read_text().splitlines()
    entry = json.loads(lines[0])
    entry["bssid"] = "FF:FF:FF:FF:FF:FF"  # tamper, hash now stale
    path.write_text(json.dumps(entry) + "\n")

    ok, msg = log.verify_chain()
    assert ok is False
    assert "tampered" in msg


def test_verify_chain_detects_deleted_entry(tmp_path):
    path = tmp_path / "evidence.jsonl"
    log = EvidenceLog(path)
    log.record("a")
    log.record("b")
    log.record("c")

    lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n")  # drop entry b

    ok, msg = log.verify_chain()
    assert ok is False
    assert "reordered" in msg or "deleted" in msg


def test_verify_chain_detects_reordering(tmp_path):
    path = tmp_path / "evidence.jsonl"
    log = EvidenceLog(path)
    log.record("a")
    log.record("b")

    lines = path.read_text().splitlines()
    path.write_text("\n".join(reversed(lines)) + "\n")

    ok, _ = log.verify_chain()
    assert ok is False


def test_empty_log_verifies_true(tmp_path):
    log = EvidenceLog(tmp_path / "evidence.jsonl")
    ok, msg = log.verify_chain()
    assert ok is True
    assert "empty" in msg


def test_reopening_log_continues_the_chain(tmp_path):
    path = tmp_path / "evidence.jsonl"
    log1 = EvidenceLog(path)
    log1.record("a")

    log2 = EvidenceLog(path)  # simulate app restart
    log2.record("b")

    ok, _ = log2.verify_chain()
    assert ok is True


def test_arbitrary_fields_round_trip(tmp_path):
    log = EvidenceLog(tmp_path / "evidence.jsonl")
    log.record("finding", source="rogue_ap", essid="Acme-Corp-WiFi", severity="critical")
    entries = log.read_all()
    assert entries[0]["source"] == "rogue_ap"
    assert entries[0]["essid"] == "Acme-Corp-WiFi"