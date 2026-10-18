# PirateDrop Service - croc CLI integration
import os
import re
import subprocess
import threading

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_CODE_RE = re.compile(
    r"(?:Code is:\s*|croc\s+|\?code=|code\s+)([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_TOKEN_RE = re.compile(r"croc-store-v1\.[A-Za-z0-9_\-\.]+")

_SEND_DONE_MARKERS = (
    "File sent",
    "Sent (",
    "Sent file",
    "Sent to",
    "Successfully sent",
)
_RECV_DONE_MARKERS = (
    "Received file written",
    "Received files",
    "Received file",
    "Verified download committed",
    "Verified download",
)


class PirateService:
    def __init__(self, croc_exe_path):
        self.croc_exe_path = croc_exe_path
        self.process = None
        self.current_code = None
        self.current_url = None
        self.cancelled = False
        self._completed = False
        self._last_error = None
        self._lock = threading.Lock()
        self._run_id = 0

    # ---- availability -------------------------------------------------
    def is_available(self):
        """Return (ok, version_or_error)."""
        if not self.croc_exe_path or not os.path.isfile(self.croc_exe_path):
            return False, "croc executable not found"
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        try:
            result = subprocess.run(
                [self.croc_exe_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                **kwargs,
            )
            output = (result.stdout or result.stderr or "").strip()
            return result.returncode == 0, output or "unknown version"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    # ---- transfers ----------------------------------------------------
    def start_send(self, paths, on_code, on_progress, on_complete, on_error, on_url=None):
        """Start a croc send transfer."""
        args = [self.croc_exe_path, "--yes", "send"] + list(paths)
        self._start(args, on_code, on_progress, on_complete, on_error, is_send=True, on_url=on_url)

    def start_store(self, paths, expiration, downloads, on_code, on_progress, on_complete, on_error, on_url=None):
        """Upload files to croc's stored mode."""
        args = [
            self.croc_exe_path,
            "store",
            "--expiration",
            str(expiration),
            "--downloads",
            str(downloads),
        ] + list(paths)
        self._start(
            args,
            on_code,
            on_progress,
            on_complete,
            on_error,
            is_send=True,
            is_store=True,
            on_url=on_url,
        )

    def start_receive(self, code, destination, on_progress, on_complete, on_error, on_code=None):
        """Start a croc receive transfer (accepts a code, link or store token)."""
        args = [self.croc_exe_path, "--yes", "--out", destination, code]
        self._start(args, on_code, on_progress, on_complete, on_error, is_send=False)

    # ---- internals ----------------------------------------------------
    def _start(self, args, on_code, on_progress, on_complete, on_error, is_send, is_store=False, on_url=None):
        self._cleanup()
        self.cancelled = False
        self._completed = False
        self.current_code = None
        self.current_url = None
        self._last_error = None
        self._run_id += 1
        run_id = self._run_id

        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            self.process = subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                **kwargs,
            )
        except Exception as e:
            on_error(str(e))
            return

        proc = self.process
        code_re = _TOKEN_RE if is_store else _CODE_RE

        # Store sends print their token/link *after* the "upload complete"
        # line, so we rely on clean process exit to signal completion.
        if not is_send:
            markers = _RECV_DONE_MARKERS
        elif is_store:
            markers = ()
        else:
            markers = _SEND_DONE_MARKERS

        def clean(line):
            return _ANSI_RE.sub("", line).strip()

        def handle(text):
            if not text:
                return

            if on_code and self.current_code is None:
                match = code_re.search(text)
                if match:
                    self.current_code = match.group(0) if is_store else match.group(1)
                    on_code(self.current_code)

            if on_url and self.current_url is None:
                match = _URL_RE.search(text)
                if match:
                    self.current_url = match.group(0).rstrip(".,)")
                    on_url(self.current_url)

            if markers and not self._completed and any(m in text for m in markers):
                with self._lock:
                    if not self._completed:
                        self._completed = True
                        on_complete()

            on_progress(text)

        def run():
            # Read every line to EOF before deciding the outcome, so late
            # output (e.g. store tokens/links) is always parsed first.
            try:
                for line in iter(proc.stdout.readline, ""):
                    text = clean(line)
                    if text:
                        self._last_error = text
                        handle(text)
            except Exception:
                pass

            try:
                returncode = proc.wait()
            except Exception:
                returncode = -1

            if self.cancelled or run_id != self._run_id:
                return
            with self._lock:
                if self._completed:
                    return
                self._completed = True
            if returncode == 0:
                on_complete()
            else:
                on_error(self._last_error or f"croc exited with code {returncode}")

        threading.Thread(target=run, daemon=True).start()

    def cancel(self):
        """Cancel the current transfer (no completion/error callback fires)."""
        with self._lock:
            self.cancelled = True
        self._run_id += 1
        self._cleanup()

    def _cleanup(self):
        """Clean up process resources without blocking indefinitely."""
        proc = self.process
        self.process = None
        if proc is None:
            return
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            pass
        for stream in (proc.stdout, proc.stderr):
            try:
                if stream:
                    stream.close()
            except Exception:
                pass

    def _parse_share_code(self, output):
        match = _CODE_RE.search(_ANSI_RE.sub("", output or ""))
        return match.group(1) if match else None
