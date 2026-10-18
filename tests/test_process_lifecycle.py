"""Categories 7, 8, 9, 12: start failures, unexpected exits, cancellation, state transitions."""

import time

from services.pirate_service import PirateService

CROC = "croc.exe"


def _send_kwargs(rec):
    return dict(
        on_code=rec.on_code, on_progress=rec.on_progress,
        on_complete=rec.on_complete, on_error=rec.on_error,
    )


def _recv_kwargs(rec):
    return dict(
        on_progress=rec.on_progress, on_complete=rec.on_complete,
        on_error=rec.on_error,
    )


# ---- 7. process-start failures ------------------------------------------
def test_popen_failure_reports_error(fake_popen, recorder):
    fake_popen.spec.exc = OSError("WinError 2: system cannot find the file")
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert recorder.error_event.wait(timeout=5)
    assert "WinError 2" in recorder.errors[0]
    assert recorder.completed_count == 0


# ---- 8. unexpected process exits ----------------------------------------
def test_nonzero_exit_reports_last_output_line(fake_popen, recorder):
    fake_popen.spec.lines = ["connecting...\n", "transfer failed: peer refused\n"]
    fake_popen.spec.returncode = 1
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\out", **_recv_kwargs(recorder))
    assert recorder.error_event.wait(timeout=5)
    assert recorder.errors == ["transfer failed: peer refused"]
    assert recorder.completed_count == 0


def test_nonzero_exit_without_output_reports_exit_code(fake_popen, recorder):
    fake_popen.spec.returncode = 9
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\out", **_recv_kwargs(recorder))
    assert recorder.error_event.wait(timeout=5)
    assert "9" in recorder.errors[0]


def test_zero_exit_completes_even_without_done_marker(fake_popen, recorder):
    fake_popen.spec.lines = ["some output\n"]
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.completed_count == 1
    assert recorder.errors == []


def test_done_marker_then_zero_exit_completes_only_once(fake_popen, recorder):
    fake_popen.spec.lines = ["File sent.\n", "closing socket\n"]
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    time.sleep(0.3)
    assert recorder.completed_count == 1


def test_receive_done_marker_completes(fake_popen, recorder):
    fake_popen.spec.lines = ["Received file written to C:\\out\\f.txt\n"]
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\out", **_recv_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert recorder.completed_count == 1


# ---- 9. cancellation and cleanup ----------------------------------------
def test_cancel_terminates_process(fake_popen, recorder):
    fake_popen.spec.block_forever = True
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert len(fake_popen.processes) == 1
    proc = fake_popen.processes[0]
    svc.cancel()
    assert proc.terminated is True
    assert svc.process is None


def test_cancel_fires_no_completion_or_error(fake_popen, recorder):
    fake_popen.spec.block_forever = True
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    svc.cancel()
    time.sleep(0.4)
    assert recorder.completed_count == 0
    assert recorder.errors == []


def test_cancel_kills_if_terminate_hangs(fake_popen, recorder):
    fake_popen.spec.block_forever = True
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\out", **_recv_kwargs(recorder))
    proc = fake_popen.processes[0]

    original_wait = proc.wait
    hanging = {"value": False}

    def wait_hook(timeout=None):
        if proc.terminated and not hanging["value"]:
            hanging["value"] = True
            raise Exception("simulated hang")  # noqa: TRY002 - forces kill path via except
        return original_wait(timeout=timeout)

    proc.wait = wait_hook
    svc.cancel()
    assert proc.terminated is True


def test_new_start_after_cancel_uses_fresh_process(fake_popen, recorder):
    fake_popen.spec.block_forever = True
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    svc.cancel()

    fake_popen.spec.block_forever = False
    fake_popen.spec.lines = ["File sent.\n"]
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert recorder.complete_event.wait(timeout=5)
    assert len(fake_popen.processes) == 2
    assert recorder.completed_count == 1


# ---- 12. state transitions ----------------------------------------------
def test_stale_thread_after_cancel_cannot_fire_callbacks(fake_popen, recorder):
    fake_popen.spec.block_forever = True
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    stale_proc = fake_popen.processes[0]
    svc.cancel()

    codes_second = []
    fake_popen.spec.block_forever = False
    fake_popen.spec.lines = ["Code is: new-111-aaa\n", "File sent.\n"]
    svc.start_send(["f2.txt"], on_code=codes_second.append,
                   on_progress=recorder.on_progress,
                   on_complete=recorder.on_complete,
                   on_error=recorder.on_error)
    assert recorder.complete_event.wait(timeout=5)

    # release the stale thread and give it a chance to misfire
    stale_proc.stdout.close()
    time.sleep(0.3)
    assert recorder.completed_count == 1
    assert recorder.errors == []
    assert codes_second == ["new-111-aaa"]


def test_cancelled_flag_resets_on_next_start(fake_popen, recorder):
    fake_popen.spec.block_forever = True
    svc = PirateService(CROC)
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    svc.cancel()
    assert svc.cancelled is True

    fake_popen.spec.block_forever = False
    svc.start_send(["f.txt"], **_send_kwargs(recorder))
    assert svc.cancelled is False
