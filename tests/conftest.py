"""Shared fixtures for PirateDrop tests."""

import os
import sys
import threading
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run real-network integration tests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return
    skip = pytest.mark.skip(reason="integration test; pass --run-integration to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


# ---- Qt ------------------------------------------------------------------
@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


# ---- fake croc process ---------------------------------------------------
class FakeStdout:
    def __init__(self, lines, block_forever=False):
        self._lines = list(lines)
        self._index = 0
        self._closed = False
        self._release = threading.Event() if block_forever else None

    def readline(self):
        if self._index < len(self._lines):
            line = self._lines[self._index]
            self._index += 1
            return line
        if self._release is not None:
            self._release.wait(timeout=10)
        return ""

    def close(self):
        self._closed = True
        if self._release is not None:
            self._release.set()


class FakeProcess:
    def __init__(self, args, lines=(), returncode=0, block_forever=False):
        self.args = list(args)
        self.returncode = returncode
        self.stdout = FakeStdout(lines, block_forever)
        self.stderr = None
        self.block_forever = block_forever
        self.terminated = False
        self.killed = False
        self._done = threading.Event()
        if not block_forever:
            self._done.set()

    def poll(self):
        if self.block_forever and not (self.terminated or self.killed):
            return None
        return self.returncode

    def wait(self, timeout=None):
        self._done.wait(timeout=timeout)
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.stdout.close()
        self._done.set()

    def kill(self):
        self.killed = True
        self.stdout.close()
        self._done.set()


@pytest.fixture
def fake_popen(monkeypatch):
    """Patch subprocess.Popen with a scriptable fake croc process."""
    created = []
    spec = SimpleNamespace(lines=(), returncode=0, block_forever=False, exc=None)

    def factory(args, **kwargs):
        if spec.exc is not None:
            raise spec.exc
        proc = FakeProcess(
            args,
            lines=spec.lines,
            returncode=spec.returncode,
            block_forever=spec.block_forever,
        )
        created.append(proc)
        return proc

    monkeypatch.setattr("subprocess.Popen", factory)
    return SimpleNamespace(spec=spec, processes=created)


class Recorder:
    """Collects PirateService callbacks and exposes wait helpers."""

    def __init__(self):
        self.codes = []
        self.urls = []
        self.progress = []
        self.errors = []
        self.completed_count = 0
        self.code_event = threading.Event()
        self.url_event = threading.Event()
        self.complete_event = threading.Event()
        self.error_event = threading.Event()

    def on_code(self, code):
        self.codes.append(code)
        self.code_event.set()

    def on_url(self, url):
        self.urls.append(url)
        self.url_event.set()

    def on_progress(self, text):
        self.progress.append(text)

    def on_complete(self):
        self.completed_count += 1
        self.complete_event.set()

    def on_error(self, text):
        self.errors.append(text)
        self.error_event.set()


@pytest.fixture
def recorder():
    return Recorder()


def start_args(service, recorder, is_send=True):
    """Return (kwargs) callback bundle for service start_* methods."""
    return dict(
        on_code=recorder.on_code,
        on_progress=recorder.on_progress,
        on_complete=recorder.on_complete,
        on_error=recorder.on_error,
        on_url=recorder.on_url,
    )


# ---- isolated config / history -------------------------------------------
@pytest.fixture
def tmp_config(tmp_path):
    from services.config import Config

    return Config(path=str(tmp_path / "settings.json"))


@pytest.fixture
def tmp_history(tmp_path):
    from services.history import HistoryStore

    return HistoryStore(path=str(tmp_path / "history.json"))
