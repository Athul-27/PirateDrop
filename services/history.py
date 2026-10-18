"""Persistent transfer history for PirateDrop."""

import json
import os
import time

from services.config import HISTORY_PATH

MAX_ENTRIES = 200


class HistoryStore:
    def __init__(self, path=HISTORY_PATH):
        self.path = path
        self.entries = []
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, list):
                self.entries = data
        except (FileNotFoundError, ValueError, OSError):
            self.entries = []

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self.entries, handle, indent=2)
        except OSError:
            pass

    def add(self, direction, items, code="", url="", outcome="success", size=""):
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "direction": direction,
            "items": items if isinstance(items, list) else [items],
            "count": len(items) if isinstance(items, list) else 1,
            "code": code,
            "url": url,
            "outcome": outcome,
            "size": size,
        }
        self.entries.insert(0, entry)
        self.entries = self.entries[:MAX_ENTRIES]
        self.save()
        return entry

    def clear(self):
        self.entries = []
        self.save()


_INSTANCE = None


def get_history():
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = HistoryStore()
    return _INSTANCE
