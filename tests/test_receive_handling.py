"""Categories 10, 13: destination conflicts, missing share codes."""

from services.pirate_service import PirateService
from ui.receive_screen import ReceiveScreen
from ui import dialogs

CROC = "croc.exe"


def test_receive_passes_yes_flag_so_conflicts_never_block_silently(fake_popen, tmp_path):
    from services.pirate_service import PirateService
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", str(tmp_path), on_progress=lambda t: None,
                      on_complete=lambda: None, on_error=lambda e: None)
    args = fake_popen.processes[0].args
    assert "--yes" in args


def test_conflict_style_error_output_reported_to_user(fake_popen, recorder):
    fake_popen.spec.lines = ["error: cannot write, destination file exists\n"]
    fake_popen.spec.returncode = 1
    svc = PirateService(CROC)
    svc.start_receive("abc-123-def", "C:\\out",
                      on_progress=recorder.on_progress,
                      on_complete=recorder.on_complete,
                      on_error=recorder.on_error)
    assert recorder.error_event.wait(timeout=5)
    assert "destination file exists" in recorder.errors[0]


def test_missing_share_code_shows_warning(qapp, monkeypatch, tmp_config, tmp_history):
    warnings = []
    monkeypatch.setattr(dialogs, "show_warning",
                        lambda parent, text, title="Warning": warnings.append((text, title)))
    monkeypatch.setattr("ui.receive_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.receive_screen.get_history", lambda: tmp_history)

    screen = ReceiveScreen()
    screen.code_input.setText("")
    screen.dest_input.setText("C:\\Downloads")
    screen.start_receive()

    assert warnings and warnings[0][1] == "No Share Code"
    assert screen.pirate_service.process is None


def test_blank_share_code_shows_warning(qapp, monkeypatch, tmp_config, tmp_history):
    warnings = []
    monkeypatch.setattr(dialogs, "show_warning",
                        lambda parent, text, title="Warning": warnings.append(title))
    monkeypatch.setattr("ui.receive_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.receive_screen.get_history", lambda: tmp_history)

    screen = ReceiveScreen()
    screen.code_input.setText("     ")
    screen.dest_input.setText("C:\\Downloads")
    screen.start_receive()

    assert warnings == ["No Share Code"]


def test_normalize_input_variants():
    assert ReceiveScreen.normalize_input("abc-123-def") == "abc-123-def"
    assert ReceiveScreen.normalize_input("  Code is: abc-123-def  ") == "abc-123-def"
    assert ReceiveScreen.normalize_input("croc-store-v1.QUJDRA.xyz.key") == "croc-store-v1.QUJDRA.xyz.key"
    assert ReceiveScreen.normalize_input("") == ""
    token = ReceiveScreen.normalize_input(
        "https://getcroc.com/s/transfer123#v1.secretkey456")
    assert token.startswith("croc-store-v1.")
    assert "transfer123" in token
    assert "secretkey456" in token
