"""Application configuration and settings persistence for PirateDrop."""

import json
import os
import sys

APP_NAME = "PirateDrop"

DEFAULTS = {
    "croc_path": "",
    "default_destination": "",
    "store_mode": False,
    "store_expiration": "1d",
    "store_downloads": 1,
    "show_security_notice": True,
    "window_geometry": "",
}


def config_dir():
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, APP_NAME)


CONFIG_DIR = config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")
HISTORY_PATH = os.path.join(CONFIG_DIR, "history.json")


class Config:
    def __init__(self, path=CONFIG_PATH):
        self.path = path
        self._data = dict(DEFAULTS)
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                for key, value in data.items():
                    if key in DEFAULTS:
                        self._data[key] = value
        except (FileNotFoundError, ValueError, OSError):
            pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2)
        except OSError:
            pass

    def get(self, key, default=None):
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key, value):
        self._data[key] = value

    def update(self, **kwargs):
        self._data.update(kwargs)
        self.save()


_INSTANCE = None


def get_config():
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = Config()
    return _INSTANCE


def bundled_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_croc_path():
    """Resolve the croc executable in priority order."""
    candidates = []

    saved = get_config().get("croc_path")
    if saved:
        candidates.append(saved)

    candidates.append(os.path.join(bundled_dir(), "croc.exe"))

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(repo_root, "croc.exe"))

    if os.name == "nt":
        candidates.append(r"c:\croc\croc.exe")
        candidates.append("croc.exe")

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    return "croc"
