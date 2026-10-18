"""Categories 14, 15: empty file selections, invalid destination paths."""

from ui.send_screen import SendScreen
from ui.receive_screen import ReceiveScreen
from ui import dialogs


def test_empty_file_selection_shows_warning(qapp, monkeypatch, tmp_config, tmp_history):
    warnings = []
    monkeypatch.setattr(dialogs, "show_warning",
                        lambda parent, text, title="Warning": warnings.append(title))
    monkeypatch.setattr("ui.send_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.send_screen.get_history", lambda: tmp_history)

    screen = SendScreen()
    assert screen.jobs == []
    screen.start_send()

    assert warnings == ["No Files"]
    assert screen.pirate_service.process is None


def test_selection_with_only_deleted_paths_shows_warning(qapp, monkeypatch, tmp_config, tmp_history, tmp_path):
    warnings = []
    monkeypatch.setattr(dialogs, "show_warning",
                        lambda parent, text, title="Warning": warnings.append(title))
    monkeypatch.setattr("ui.send_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.send_screen.get_history", lambda: tmp_history)

    gone = str(tmp_path / "already-deleted.txt")
    screen = SendScreen()
    screen.jobs.append({"paths": [gone]})
    # _existing_paths filters to files that still exist -> empty
    screen.start_send()

    assert warnings == ["No Files"]


def test_no_destination_shows_warning(qapp, monkeypatch, tmp_config, tmp_history):
    warnings = []
    monkeypatch.setattr(dialogs, "show_warning",
                        lambda parent, text, title="Warning": warnings.append(title))
    monkeypatch.setattr("ui.receive_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.receive_screen.get_history", lambda: tmp_history)

    screen = ReceiveScreen()
    screen.dest_input.setText("")
    screen.code_input.setText("abc-123-def")
    screen.start_receive()

    assert warnings == ["No Destination"]
    assert screen.pirate_service.process is None


def test_whitespace_destination_shows_warning(qapp, monkeypatch, tmp_config, tmp_history):
    warnings = []
    monkeypatch.setattr(dialogs, "show_warning",
                        lambda parent, text, title="Warning": warnings.append(title))
    monkeypatch.setattr("ui.receive_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.receive_screen.get_history", lambda: tmp_history)

    screen = ReceiveScreen()
    screen.dest_input.setText("   ")
    screen.code_input.setText("abc-123-def")
    screen.start_receive()

    assert warnings == ["No Destination"]
