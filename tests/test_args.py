"""Categories 3, 4, 5: paths with spaces, unicode filenames, argument construction."""

import pytest

from services.pirate_service import PirateService

CROC = "C:\\tools\\croc.exe"


def test_send_argument_construction(fake_popen, recorder):
    svc = PirateService(CROC)
    svc.start_send(["a.txt", "b.txt"], **dict(
        on_code=recorder.on_code, on_progress=recorder.on_progress,
        on_complete=recorder.on_complete, on_error=recorder.on_error,
    ))
    args = fake_popen.processes[0].args
    assert args == [CROC, "--yes", "send", "a.txt", "b.txt"]


def test_store_argument_construction(fake_popen, recorder):
    svc = PirateService(CROC)
    svc.start_store(["a.txt"], "1d", 3, **dict(
        on_code=recorder.on_code, on_progress=recorder.on_progress,
        on_complete=recorder.on_complete, on_error=recorder.on_error,
    ))
    args = fake_popen.processes[0].args
    assert args == [CROC, "store", "--expiration", "1d", "--downloads", "3", "a.txt"]


def test_receive_argument_construction(fake_popen, recorder):
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\Downloads", **dict(
        on_progress=recorder.on_progress, on_complete=recorder.on_complete,
        on_error=recorder.on_error,
    ))
    args = fake_popen.processes[0].args
    assert args == [CROC, "--yes", "--out", "C:\\Downloads", "abc-123-def"]


def test_path_with_spaces_stays_single_argument(fake_popen, recorder):
    svc = PirateService(CROC)
    path = "C:\\My Documents\\annual report 2026.pdf"
    svc.start_send([path], **dict(
        on_code=recorder.on_code, on_progress=recorder.on_progress,
        on_complete=recorder.on_complete, on_error=recorder.on_error,
    ))
    args = fake_popen.processes[0].args
    assert args[-1] == path
    assert path in args
    assert len([a for a in args if "annual" in a]) == 1


def test_unicode_filenames_stay_single_arguments(fake_popen, recorder):
    svc = PirateService(CROC)
    paths = ["café-übung.txt", "日本語ファイル.txt", "файл-данные.bin"]
    svc.start_send(paths, **dict(
        on_code=recorder.on_code, on_progress=recorder.on_progress,
        on_complete=recorder.on_complete, on_error=recorder.on_error,
    ))
    args = fake_popen.processes[0].args
    for path in paths:
        assert path in args


@pytest.mark.parametrize("path", [
    "C:\\Program Files\\app\\data.bin",
    "\\\\network share\\folder\\file.txt",
    "C:\\trailing space \\file.txt",
])
def test_awkward_paths_not_split(fake_popen, recorder, path):
    svc = PirateService(CROC)
    svc.start_send([path], **dict(
        on_code=recorder.on_code, on_progress=recorder.on_progress,
        on_complete=recorder.on_complete, on_error=recorder.on_error,
    ))
    assert fake_popen.processes[0].args[-1] == path
