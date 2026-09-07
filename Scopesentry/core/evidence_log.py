"""Append-only, hash-chained evidence log.

Every entry embeds the hash of the previous entry and is itself hashed over
its own canonical JSON (including that embedded prev_hash). verify_chain()
recomputes the same hash the same way and also checks that each entry's
embedded prev_hash matches the hash actually produced by the entry before it
— so both tampering with a single entry *and* deleting/reordering entries
are detected.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

GENESIS_HASH = "0" * 64


def _canonical(entry: dict) -> str:
    """Deterministic JSON encoding used for hashing — same fields, same order,
    every time, on both record() and verify_chain()."""
    return json.dumps(entry, sort_keys=True, separators=(",", ":"))


def _hash_entry(entry_without_hash: dict) -> str:
    return hashlib.sha256(_canonical(entry_without_hash).encode("utf-8")).hexdigest()


class EvidenceLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._prev_hash = self._last_hash()

    def _last_hash(self) -> str:
        if not self.path.exists():
            return GENESIS_HASH
        last_line = None
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last_line = line
        if not last_line:
            return GENESIS_HASH
        return json.loads(last_line)["entry_hash"]

    def record(self, event: str, **fields) -> str:
        """Append one entry. Returns the new entry's hash."""
        entry = {
            "ts": datetime.now().isoformat(),
            "event": event,
            "prev_hash": self._prev_hash,
            **fields,
        }
        entry_hash = _hash_entry(entry)
        full_entry = {**entry, "entry_hash": entry_hash}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(full_entry, sort_keys=True) + "\n")
        self._prev_hash = entry_hash
        return entry_hash

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def verify_chain(self) -> tuple[bool, str]:
        """Walk the file from the top and confirm every entry's hash is
        correct and every prev_hash link matches. Returns (ok, message)."""
        expected_prev = GENESIS_HASH
        entries = self.read_all()
        if not entries:
            return True, "log is empty"

        for i, entry in enumerate(entries):
            if "entry_hash" not in entry:
                return False, f"entry {i} is missing entry_hash"
            claimed_hash = entry["entry_hash"]
            entry_without_hash = {k: v for k, v in entry.items() if k != "entry_hash"}

            if entry_without_hash.get("prev_hash") != expected_prev:
                return False, (
                    f"entry {i} has prev_hash {entry_without_hash.get('prev_hash')!r}, "
                    f"expected {expected_prev!r} — log was reordered, an entry was "
                    f"deleted, or this entry was edited"
                )

            recomputed = _hash_entry(entry_without_hash)
            if recomputed != claimed_hash:
                return False, f"entry {i} hash does not match its contents — entry was tampered with"

            expected_prev = claimed_hash

        return True, f"chain intact across {len(entries)} entries"