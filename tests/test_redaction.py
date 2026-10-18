"""Category 16: diagnostic-log redaction — no raw croc output persisted to disk."""

import os

from services.pirate_service import PirateService
from services.history import HistoryStore

CROC = "croc.exe"

SENSITIVE_LINE = "token: croc-store-v1.SECRETBASE64.transfer-id.super-secret-key"


def test_failed_transfer_writes_no_files_to_disk(fake_popen, tmp_path, monkeypatch):
    fake_popen.spec.lines = [SENSITIVE_LINE + "\n", "transfer aborted\n"]
    fake_popen.spec.returncode = 1

    monkeypatch.chdir(tmp_path)
    svc = PirateService(CROC)
    done = {"ok": False}
    svc.start_receive("abc-123-def", str(tmp_path / "out"),
                      on_progress=lambda t: None,
                      on_complete=lambda: done.update(ok=True),
                      on_error=lambda e: None)

    import time
    end = time.time() + 5
    while time.time() < end and not done["ok"] and svc.process is not None:
        time.sleep(0.05)
    time.sleep(0.2)

    assert os.listdir(tmp_path) == []


def test_history_entries_contain_only_whitelisted_fields(tmp_history):
    entry = tmp_history.add(
        direction="send",
        items=["C:\\file.txt"],
        code="abc-123-def",
        url="https://getcroc.com/s/x#v1.y",
        outcome="success",
        size="10 MB",
    )
    expected = {"time", "direction", "items", "count", "code", "url", "outcome", "size"}
    assert set(entry.keys()) == expected


def test_history_is_capped_at_max_entries(tmp_history):
    from services.history import MAX_ENTRIES

    for i in range(MAX_ENTRIES + 25):
        tmp_history.add(direction="send", items=[f"f{i}.txt"])
    assert len(tmp_history.entries) == MAX_ENTRIES


def test_corrupt_history_file_recovers_to_empty(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{not valid json[", encoding="utf-8")
    store = HistoryStore(path=str(path))
    assert store.entries == []
