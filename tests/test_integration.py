"""Integration: real local transfer with bundled croc.exe (run with --run-integration).

Requires network access to croc's default relay. Honest reporting per plan:
this test either verifies a real byte-for-byte transfer or fails loudly.
"""

import os
import threading
import time

import pytest

from services.pirate_service import PirateService

pytestmark = pytest.mark.integration

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CROC = os.path.join(REPO_ROOT, "croc.exe")

PAYLOAD = b"piratedrop-integration-payload-" + os.urandom(64)


def test_real_send_receive_roundtrip(tmp_path):
    if not os.path.isfile(CROC):
        pytest.skip("croc.exe not bundled")

    src = tmp_path / "payload.bin"
    src.write_bytes(PAYLOAD)
    dest = tmp_path / "received"
    dest.mkdir()

    codes = []
    code_event = threading.Event()
    send_done = threading.Event()
    send_errors = []
    recv_done = threading.Event()
    recv_errors = []

    sender = PirateService(CROC)
    sender.start_send(
        [str(src)],
        on_code=lambda c: (codes.append(c), code_event.set()),
        on_progress=lambda t: None,
        on_complete=send_done.set,
        on_error=lambda e: (send_errors.append(e), send_done.set()),
    )
    assert code_event.wait(timeout=90), f"no share code received: {send_errors}"
    code = codes[0]

    receiver = PirateService(CROC)
    receiver.start_receive(
        code,
        str(dest),
        on_progress=lambda t: None,
        on_complete=recv_done.set,
        on_error=lambda e: (recv_errors.append(e), recv_done.set()),
    )
    finished = recv_done.wait(timeout=120)
    if not finished:
        receiver.cancel()
        pytest.fail(f"receive timed out: {recv_errors}")

    time.sleep(0.3)
    assert not send_errors, f"send failed: {send_errors}"
    assert not recv_errors, f"receive failed: {recv_errors}"

    received = dest / "payload.bin"
    assert received.is_file(), f"file missing in {list(dest.iterdir())}"
    assert received.read_bytes() == PAYLOAD
