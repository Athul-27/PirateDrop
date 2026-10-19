"""Tests for the UI enhancements: open-folder, empty-state hint, size summary, sparkline."""

from ui.send_screen import SendScreen, format_size, parse_speed_mb_s
from ui.receive_screen import ReceiveScreen
from ui.sparkline import SpeedSparkline
from ui import dialogs


# ---- format_size ---------------------------------------------------------
def test_format_size_units():
    assert format_size(0) == "0 B"
    assert format_size(512) == "512 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1536) == "1.5 KB"
    assert format_size(1024 ** 2) == "1.0 MB"
    assert format_size(1024 ** 3) == "1.0 GB"
    assert format_size(1024 ** 4) == "1.0 TB"


# ---- parse_speed_mb_s ----------------------------------------------------
def test_parse_speed_mb_s():
    assert parse_speed_mb_s("1.5 MB/s") == 1.5
    assert parse_speed_mb_s("2 GB/s") == 2048.0
    assert abs(parse_speed_mb_s("1024 KB/s") - 1.0) < 1e-9
    assert parse_speed_mb_s("500 KB/s") == 500 / 1024
    assert parse_speed_mb_s("") is None
    assert parse_speed_mb_s(None) is None
    assert parse_speed_mb_s("no speed here") is None


# ---- SpeedSparkline ------------------------------------------------------
def test_sparkline_collects_and_clears(qapp):
    chart = SpeedSparkline()
    chart.add_sample(1.5)
    chart.add_sample(2.5, at=2.0)
    assert len(chart._samples) == 2
    chart.add_sample(None)
    chart.add_sample(-1)
    assert len(chart._samples) == 2
    chart.clear_data()
    assert len(chart._samples) == 0


def test_sparkline_caps_points(qapp):
    from ui.sparkline import MAX_POINTS

    chart = SpeedSparkline()
    for i in range(MAX_POINTS + 40):
        chart.add_sample(1.0, at=float(i))
    assert len(chart._samples) == MAX_POINTS


# ---- Receive: Open Folder ------------------------------------------------
def test_open_folder_hidden_until_success(qapp, monkeypatch, tmp_config, tmp_history, tmp_path):
    shown = []
    monkeypatch.setattr(dialogs, "show_info",
                        lambda parent, text, title="Info": shown.append(title))
    monkeypatch.setattr("ui.receive_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.receive_screen.get_history", lambda: tmp_history)
    monkeypatch.setattr("ui.receive_screen.resolve_croc_path", lambda: "croc.exe")

    screen = ReceiveScreen()
    assert screen.open_folder_btn.isVisibleTo(screen) is False

    screen.dest_input.setText(str(tmp_path))
    screen.code_input.setText("abc-123-def")
    screen.on_receive_complete()
    assert screen.open_folder_btn.isVisibleTo(screen) is True

    screen.reset_all()
    assert screen.open_folder_btn.isVisibleTo(screen) is False


def test_open_destination_noop_on_missing_folder(qapp, monkeypatch, tmp_config, tmp_history):
    calls = []
    monkeypatch.setattr("ui.receive_screen.os.startfile",
                        lambda path: calls.append(path), raising=False)
    monkeypatch.setattr("ui.receive_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.receive_screen.get_history", lambda: tmp_history)

    screen = ReceiveScreen()
    screen.dest_input.setText("C:\\does\\not\\exist\\anywhere")
    screen.open_destination()
    assert calls == []


# ---- Send: empty-state hint + size summary -------------------------------
def test_empty_state_hint_and_size_summary(qapp, monkeypatch, tmp_config, tmp_history, tmp_path):
    monkeypatch.setattr("ui.send_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.send_screen.get_history", lambda: tmp_history)

    screen = SendScreen()
    assert screen.list_hint.isVisibleTo(screen) is True
    assert screen.size_summary_label.text() == ""

    file_path = tmp_path / "data.bin"
    file_path.write_bytes(b"x" * 2048)
    screen._add_paths([str(file_path)])

    assert screen.list_hint.isVisibleTo(screen) is False
    assert "1 file" in screen.size_summary_label.text()
    assert "2.0 KB" in screen.size_summary_label.text()

    screen.clear_all()
    assert screen.list_hint.isVisibleTo(screen) is True
    assert screen.size_summary_label.text() == ""


def test_size_summary_counts_multiple_files(qapp, monkeypatch, tmp_config, tmp_history, tmp_path):
    monkeypatch.setattr("ui.send_screen.get_config", lambda: tmp_config)
    monkeypatch.setattr("ui.send_screen.get_history", lambda: tmp_history)

    screen = SendScreen()
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_bytes(b"a" * 1024)
    second.write_bytes(b"b" * 1024)
    screen._add_paths([str(first), str(second)])
    assert "2 files" in screen.size_summary_label.text()


# ---- config default ------------------------------------------------------
def test_window_geometry_default_present(tmp_config):
    assert tmp_config.get("window_geometry") == ""
