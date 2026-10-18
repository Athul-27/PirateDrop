"""Parses croc progress lines into structured values."""

import re

_PERCENT_RE = re.compile(r"(\d{1,3})%")
_PAREN_RE = re.compile(r"\(([^,)]+),\s*([^)]+)\)")
_ETA_RE = re.compile(r"\[([^\[\]]+?):([^\[\]]+?)\]")


def parse_progress(text):
    """Return a dict with any of: percent, size, speed, elapsed, eta."""
    result = {}
    if not text:
        return result

    match = _PERCENT_RE.search(text)
    if match:
        result["percent"] = int(match.group(1))

    match = _PAREN_RE.search(text)
    if match:
        result["size"] = match.group(1).strip()
        result["speed"] = match.group(2).strip()

    match = _ETA_RE.search(text)
    if match:
        result["elapsed"] = match.group(1).strip()
        result["eta"] = match.group(2).strip()

    return result


def format_stats(parsed):
    """Build a compact human-readable stats string from parsed progress."""
    parts = []
    if "percent" in parsed:
        parts.append(f"{parsed['percent']}%")
    if "size" in parsed:
        parts.append(parsed["size"])
    if "speed" in parsed:
        parts.append(parsed["speed"])
    if "eta" in parsed:
        parts.append(f"ETA {parsed['eta']}")
    return "  •  ".join(parts)
