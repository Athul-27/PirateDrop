import base64
import os
import re

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QProgressBar,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QObject

from services.pirate_service import PirateService
from services.config import get_config, resolve_croc_path
from services.progress import parse_progress, format_stats
from services.history import get_history
from ui import dialogs

_TOKEN_RE = re.compile(r"croc-store-v1\.[A-Za-z0-9_\-\.]+")
_CODE_RE = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+")
_STORE_URL_RE = re.compile(r"https?://getcroc\.com/s/([A-Za-z0-9_\-]+)#v1\.([A-Za-z0-9_\-]+)")
_STORE_HOST_B64 = base64.b64encode(b"https://getcroc.com").decode().rstrip("=")


class _ReceiveSignals(QObject):
    progress = Signal(str)
    completed = Signal()
    failed = Signal(str)


class ReceiveScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.config = get_config()
        self.pirate_service = PirateService(resolve_croc_path())
        self.history = get_history()
        self.signals = _ReceiveSignals()
        self.signals.progress.connect(self.on_progress_update)
        self.signals.completed.connect(self.on_receive_complete)
        self.signals.failed.connect(self.on_receive_error)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        code_label = QLabel("Share Code / Link / Token:")
        code_label.setObjectName("sectionLabel")
        layout.addWidget(code_label)

        code_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setObjectName("shareCode")
        self.code_input.setPlaceholderText("Paste code, link or store token...")
        self.paste_btn = QPushButton("Paste")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)
        code_layout.addWidget(self.code_input, 1)
        code_layout.addWidget(self.paste_btn)
        layout.addLayout(code_layout)

        dest_label = QLabel("Destination Folder:")
        dest_label.setObjectName("sectionLabel")
        layout.addWidget(dest_label)

        dest_layout = QHBoxLayout()
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Select destination folder...")
        self.dest_input.setReadOnly(True)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_destination)
        dest_layout.addWidget(self.dest_input, 1)
        dest_layout.addWidget(self.browse_btn)
        layout.addLayout(dest_layout)

        default_dest = self.config.get("default_destination")
        if default_dest:
            self.dest_input.setText(default_dest)

        action_layout = QHBoxLayout()
        self.receive_btn = QPushButton("RECEIVE FILES")
        self.receive_btn.setObjectName("primaryButton")
        self.receive_btn.clicked.connect(self.start_receive)
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.clicked.connect(self.cancel_receive)
        self.cancel_btn.setVisible(False)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_all)
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.open_destination)
        self.open_folder_btn.setVisible(False)
        action_layout.addWidget(self.receive_btn, 1)
        action_layout.addWidget(self.cancel_btn)
        action_layout.addWidget(self.reset_btn)
        action_layout.addWidget(self.open_folder_btn)
        layout.addLayout(action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.stats_label = QLabel("")
        layout.addWidget(self.stats_label)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

    # ---- helpers ------------------------------------------------------
    def _set_busy(self, busy):
        for widget in (self.receive_btn, self.paste_btn, self.browse_btn, self.reset_btn, self.open_folder_btn):
            widget.setEnabled(not busy)
        self.code_input.setEnabled(not busy)
        self.dest_input.setEnabled(not busy)
        self.cancel_btn.setVisible(busy)

    @staticmethod
    def normalize_input(text):
        text = text.strip()
        token = _TOKEN_RE.search(text)
        if token:
            return token.group(0)
        store_url = _STORE_URL_RE.search(text)
        if store_url:
            transfer_id, key = store_url.group(1), store_url.group(2)
            return f"croc-store-v1.{_STORE_HOST_B64}.{transfer_id}.{key}"
        code = _CODE_RE.search(text)
        if code:
            return code.group(0)
        return text

    def paste_from_clipboard(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.code_input.setText(text)

    def browse_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_input.setText(folder)

    # ---- receive ------------------------------------------------------
    def start_receive(self):
        code = self.normalize_input(self.code_input.text())
        destination = self.dest_input.text().strip()

        if not code:
            dialogs.show_warning(self, "Please enter a share code, link or token.", "No Share Code")
            return
        if not destination:
            dialogs.show_warning(self, "Please select a destination folder.", "No Destination")
            return

        self.pirate_service.croc_exe_path = resolve_croc_path()
        ok, info = self.pirate_service.is_available()
        if not ok:
            dialogs.show_error(
                self,
                f"croc is not available.\n{info}\n\nCheck the path in Settings.",
                "croc not found",
            )
            return

        self._set_busy(True)
        self.open_folder_btn.setVisible(False)
        self.status_label.setText("Connecting...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.stats_label.setText("")

        self.pirate_service.start_receive(
            code,
            destination,
            on_progress=self.signals.progress.emit,
            on_complete=self.signals.completed.emit,
            on_error=self.signals.failed.emit,
        )

    def on_progress_update(self, message):
        parsed = parse_progress(message)
        if parsed:
            if "percent" in parsed:
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(parsed["percent"])
            stats = format_stats(parsed)
            if stats:
                self.stats_label.setText(stats)
            if "percent" in parsed or "speed" in parsed:
                return
        self.status_label.setText(message)

    def open_destination(self):
        destination = self.dest_input.text().strip()
        if destination and os.path.isdir(destination):
            os.startfile(destination)

    def on_receive_complete(self):
        self.status_label.setText("Transfer completed successfully!")
        self.progress_bar.setVisible(False)
        self.stats_label.setText("")
        self._set_busy(False)
        self.open_folder_btn.setVisible(True)
        self.history.add(
            direction="receive",
            items=[self.dest_input.text().strip().split("\\")[-1] or "files"],
            code=self.normalize_input(self.code_input.text()),
            outcome="success",
        )
        dialogs.show_info(self, "Files received successfully!", "Transfer Complete")

    def on_receive_error(self, error):
        self.status_label.setText(f"Error: {error}")
        self.progress_bar.setVisible(False)
        self.stats_label.setText("")
        self._set_busy(False)
        self.open_folder_btn.setVisible(False)
        dialogs.show_error(self, error, "Transfer Error")

    def cancel_receive(self):
        self.pirate_service.cancel()
        self.status_label.setText("Transfer cancelled.")
        self.progress_bar.setVisible(False)
        self.stats_label.setText("")
        self._set_busy(False)
        self.open_folder_btn.setVisible(False)

    def reset_all(self):
        self.pirate_service.cancel()
        self.code_input.clear()
        self.dest_input.setText(self.config.get("default_destination") or "")
        self.status_label.setText("Ready")
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.stats_label.setText("")
        self._set_busy(False)
        self.open_folder_btn.setVisible(False)

    def closeEvent(self, event):
        self.pirate_service.cancel()
        event.accept()
