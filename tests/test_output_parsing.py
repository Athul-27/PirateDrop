"""Categories 1, 2, 6, 11: share-code extraction, ANSI stripping, output handling, progress parsing."""

from services.pirate_service import PirateService
from services.progress import parse_progress, format_stats

CROC = "croc.exe"


def _send_kwargs(rec):
    return dict(
        on_code=rec.on_code, on_progress=rec.on_progress,
        on_complete=rec.on_complete, on_error=rec.on_error,
        on_url=rec.on_url,
    )


# ---- 1. share-code extraction -------------------------------------------
def test_extract_code_from_code_is_line(fake_popen, recorder):
    fake_popen.spec.lines = ["Code is: alpha-123-beta\n"]
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.codes == ["alpha-123-beta"]


def test_extract_code_from_url_line(fake_popen, recorder):
    fake_popen.spec.lines = ["send this link: https://croc.app/?code=zzz-999-yyy\n"]
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.codes == ["zzz-999-yyy"]


def test_first_code_wins_only_fires_once(fake_popen, recorder):
    fake_popen.spec.lines = [
        "Code is: first-111-aaa\n",
        "reminder: Code is: second-222-bbb\n",
    ]
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.codes == ["first-111-aaa"]


def test_store_token_extracted_as_full_token(fake_popen, recorder):
    fake_popen.spec.lines = [
        "upload complete\n",
        "croc-store-v1.QUJDRA.xyz-123.secretkey\n",
    ]
    svc = PirateService(CROC)
    svc.start_store(["f.txt"], "1d", 1, **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.codes == ["croc-store-v1.QUJDRA.xyz-123.secretkey"]


def test_url_extracted_and_rstripped(fake_popen, recorder):
    fake_popen.spec.lines = ["share: https://getcroc.com/s/abc#v1.key.\n"]
    svc = PirateService(CROC)
    svc.start_store(["f.txt"], "1d", 1, **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.urls == ["https://getcroc.com/s/abc#v1.key"]


# ---- 2. ANSI stripping ---------------------------------------------------
def test_ansi_codes_stripped_before_code_extraction(fake_popen, recorder):
    fake_popen.spec.lines = ["\x1b[1;32mCode is: clean-777-code\x1b[0m\n"]
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.codes == ["clean-777-code"]


def test_ansi_codes_stripped_from_progress_lines(fake_popen, recorder):
    fake_popen.spec.lines = ["\x1b[33msending...\x1b[0m\n", "\x1b[32mdone\x1b[0m\n"]
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\out", **dict(
        on_progress=recorder.on_progress, on_complete=recorder.on_complete,
        on_error=recorder.on_error,
    ))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.progress == ["sending...", "done"]


# ---- 6. stdout/stderr line handling --------------------------------------
def test_all_output_lines_delivered_in_order(fake_popen, recorder):
    fake_popen.spec.lines = ["one\n", "two\n", "three\n"]
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\out", **dict(
        on_progress=recorder.on_progress, on_complete=recorder.on_complete,
        on_error=recorder.on_error,
    ))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.progress == ["one", "two", "three"]


def test_blank_and_whitespace_only_lines_skipped(fake_popen, recorder):
    fake_popen.spec.lines = ["\n", "   \n", "real\n", "\n"]
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\out", **dict(
        on_progress=recorder.on_progress, on_complete=recorder.on_complete,
        on_error=recorder.on_error,
    ))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.progress == ["real"]


# ---- 11. progress parsing ------------------------------------------------
def test_parse_percent():
    assert parse_progress("42%") == {"percent": 42}
    assert parse_progress("  100% complete") == {"percent": 100}


def test_parse_size_and_speed():
    parsed = parse_progress("(1.2 GB, 45.6 MB/s)")
    assert parsed == {"size": "1.2 GB", "speed": "45.6 MB/s"}


def test_parse_eta():
    parsed = parse_progress("[10:20]")
    assert parsed == {"elapsed": "10", "eta": "20"}


def test_parse_combined_line():
    parsed = parse_progress("55% (2.0 MB, 1.0 MB/s) [01:02]")
    assert parsed["percent"] == 55
    assert parsed["size"] == "2.0 MB"
    assert parsed["speed"] == "1.0 MB/s"
    assert parsed["elapsed"] == "01"
    assert parsed["eta"] == "02"


def test_parse_empty_and_unrelated():
    assert parse_progress("") == {}
    assert parse_progress(None) == {}
    assert parse_progress("connection established") == {}


def test_format_stats():
    assert format_stats({}) == ""
    assert format_stats({"percent": 10}) == "10%"
    assert format_stats({"percent": 10, "size": "2 MB", "speed": "1 MB/s", "eta": "0:05"}) == (
        "10%  •  2 MB  •  1 MB/s  •  ETA 0:05"
    )
