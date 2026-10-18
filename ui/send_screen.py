from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QComboBox,
    QSpinBox,
    QProgressBar,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from services.pirate_service import PirateService
from services.config import get_config, resolve_croc_path
from services.progress import parse_progress, format_stats
from services.history import get_history
from ui import dialogs

STORE_EXPIRATIONS = ["30m", "90m", "12h", "1d", "3d", "1w", "2w"]


class _SendSignals(QObject):
    code = Signal(str)
    url = Signal(str)
    progress = Signal(str)
    completed = Signal()
    failed = Signal(str)


class SendScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.config = get_config()
        self.pirate_service = PirateService(resolve_croc_path())
        self.history = get_history()
        self.signals = _SendSignals()
        self.signals.code.connect(self.on_share_code_received)
        self.signals.url.connect(self.on_share_url_received)
        self.signals.progress.connect(self.on_progress_update)
        self.signals.completed.connect(self.on_job_complete)
        self.signals.failed.connect(self.on_job_error)
        self.jobs = []
        self.current_job = None
        self.init_ui()

    # ---- UI -----------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        file_layout = QHBoxLayout()
        self.file_btn = QPushButton("Select Files")
        self.file_btn.clicked.connect(self.select_files)
        self.folder_btn = QPushButton("Select Folder")
        self.folder_btn.clicked.connect(self.select_folder)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_all)
        file_layout.addWidget(self.file_btn)
        file_layout.addWidget(self.folder_btn)
        file_layout.addSpacing(12)
        file_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Direct", "Stored"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        file_layout.addWidget(self.mode_combo)

        self.exp_label = QLabel("Expires:")
        self.exp_combo = QComboBox()
        self.exp_combo.addItems(STORE_EXPIRATIONS)
        self.exp_combo.setCurrentText(str(self.config.get("store_expiration") or "1d"))
        self.dl_label = QLabel("Downloads:")
        self.dl_spin = QSpinBox()
        self.dl_spin.setRange(1, 20)
        self.dl_spin.setValue(int(self.config.get("store_downloads") or 1))
        self.store_widgets = [self.exp_label, self.exp_combo, self.dl_label, self.dl_spin]
        for widget in self.store_widgets:
            file_layout.addWidget(widget)
        file_layout.addStretch()
        file_layout.addWidget(self.remove_btn)
        file_layout.addWidget(self.clear_btn)
        layout.addLayout(file_layout)

        list_label = QLabel("Files to send  (drag & drop supported):")
        list_label.setObjectName("sectionLabel")
        layout.addWidget(list_label)
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setMinimumHeight(150)
        layout.addWidget(self.file_list)

        QShortcut(QKeySequence(Qt.Key_Delete), self.file_list, activated=self.remove_selected)

        # Action buttons
        action_layout = QHBoxLayout()
        self.send_btn = QPushButton("SEND FILES")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.clicked.connect(self.start_send)
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.clicked.connect(self.cancel_send)
        self.cancel_btn.setVisible(False)
        action_layout.addWidget(self.send_btn, 1)
        action_layout.addWidget(self.cancel_btn)
        layout.addLayout(action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.stats_label = QLabel("")
        self.stats_label.setObjectName("statsLabel")
        layout.addWidget(self.stats_label)

        # Share code / URL
        share_layout = QHBoxLayout()
        share_layout.addWidget(QLabel("Share Code:"))
        self.share_code_display = QLineEdit()
        self.share_code_display.setObjectName("shareCode")
        self.share_code_display.setReadOnly(True)
        self.copy_btn = QPushButton("Copy Code")
        self.copy_btn.setFixedSize(120, 36)
        self.copy_btn.clicked.connect(self.copy_share_code)
        share_layout.addWidget(self.share_code_display, 1)
        share_layout.addWidget(self.copy_btn)
        layout.addLayout(share_layout)

        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Share URL:"))
        self.share_url_display = QLineEdit()
        self.share_url_display.setObjectName("shareUrl")
        self.share_url_display.setReadOnly(True)
        self.share_url_display.setPlaceholderText("A download link will appear here...")
        self.copy_url_btn = QPushButton("Copy URL")
        self.copy_url_btn.setFixedSize(120, 36)
        self.copy_url_btn.clicked.connect(self.copy_share_url)
        url_layout.addWidget(self.share_url_display, 1)
        url_layout.addWidget(self.copy_url_btn)
        layout.addLayout(url_layout)

        # Queue
        queue_header = QHBoxLayout()
        self.queue_label = QLabel("Queue:")
        self.queue_clear_btn = QPushButton("Clear Queue")
        self.queue_clear_btn.setFixedSize(120, 36)
        self.queue_clear_btn.clicked.connect(self.clear_queue)
        queue_header.addWidget(self.queue_label)
        queue_header.addStretch()
        queue_header.addWidget(self.queue_clear_btn)
        layout.addLayout(queue_header)
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(90)
        self.queue_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.queue_list.itemDoubleClicked.connect(self.remove_queue_item)
        layout.addWidget(self.queue_list)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

        self.on_mode_changed(0)
        self.refresh_queue()

    # ---- helpers ------------------------------------------------------
    def _store_selected(self):
        return self.mode_combo.currentIndex() == 1

    def on_mode_changed(self, index):
        stored = index == 1
        for widget in self.store_widgets:
            widget.setVisible(stored)
        self.share_code_display.setPlaceholderText("Store token will appear here..." if stored else "")

    def _batch_description(self, job):
        count = len(job["paths"])
        mode = "Stored" if job["store"] else "Direct"
        return f"[{mode}] {count} item(s)"

    def refresh_queue(self):
        self.queue_list.clear()
        for job in self.jobs:
            QListWidgetItem(self._batch_description(job), self.queue_list)
        active = self._batch_description(self.current_job) if self.current_job else None
        self.queue_label.setText(f"Queue ({len(self.jobs)} pending)" + (f"  |  Sending: {active}" if active else ""))

    def _set_busy(self, busy):
        for widget in (self.file_btn, self.folder_btn, self.clear_btn, self.mode_combo):
            widget.setEnabled(not busy)
        self.cancel_btn.setVisible(busy)

    # ---- file list ----------------------------------------------------
    def _existing_paths(self):
        return [self.file_list.item(i).text() for i in range(self.file_list.count())]

    def _add_paths(self, paths):
        existing = set(self._existing_paths())
        for path in paths:
            if path and path not in existing:
                self.file_list.addItem(path)
                existing.add(path)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Send")
        if files:
            self._add_paths(files)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Send")
        if folder:
            self._add_paths([folder])

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def clear_all(self):
        self.file_list.clear()
        self.status_label.setText("Ready")

    def clear_queue(self):
        self.jobs.clear()
        self.refresh_queue()

    def remove_queue_item(self, item):
        row = self.queue_list.row(item)
        if 0 <= row < len(self.jobs):
            del self.jobs[row]
            self.refresh_queue()

    # ---- drag and drop ------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self._add_paths(paths)
            event.acceptProposedAction()

    # ---- sending / queue ----------------------------------------------
    def start_send(self):
        paths = self._existing_paths()
        if not paths:
            dialogs.show_warning(self, "Please select files or folders to send.", "No Files")
            return

        ok, info = self.pirate_service.is_available()
        if not ok:
            dialogs.show_error(
                self,
                f"croc is not available.\n{info}\n\nCheck the path in Settings.",
                "croc not found",
            )
            return

        job = {
            "paths": paths,
            "store": self.mode_combo.currentIndex() == 1,
            "expiration": self.exp_combo.currentText(),
            "downloads": self.dl_spin.value(),
        }

        if self.current_job is not None:
            self.jobs.append(job)
            self.refresh_queue()
            self.status_label.setText("Added to queue.")
            return

        self._start_job(job)

    def _start_job(self, job):
        self.current_job = job
        self.share_code_display.clear()
        self.share_url_display.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.stats_label.setText("")
        self._set_busy(True)
        self.refresh_queue()
        self.status_label.setText("Preparing...")

        self.pirate_service.croc_exe_path = resolve_croc_path()
        callbacks = dict(
            on_code=self.signals.code.emit,
            on_progress=self.signals.progress.emit,
            on_complete=self.signals.completed.emit,
            on_error=self.signals.failed.emit,
            on_url=self.signals.url.emit,
        )
        if job["store"]:
            self.pirate_service.start_store(
                job["paths"], job["expiration"], job["downloads"], **callbacks
            )
        else:
            self.pirate_service.start_send(job["paths"], **callbacks)

    def _finish_job(self, outcome):
        job = self.current_job
        if job:
            self.history.add(
                direction="stored" if job["store"] else "send",
                items=[p.split("\\")[-1] for p in job["paths"]],
                code=self.share_code_display.text(),
                url=self.share_url_display.text(),
                outcome=outcome,
            )
        self.current_job = None
        if self.jobs:
            next_job = self.jobs.pop(0)
            self.refresh_queue()
            self._start_job(next_job)
        else:
            self._set_busy(False)
            self.progress_bar.setVisible(False)
            self.refresh_queue()

    # ---- callbacks ----------------------------------------------------
    def on_share_code_received(self, code):
        self.share_code_display.setText(code)
        if self.current_job and not self.current_job["store"]:
            self.status_label.setText("Waiting for receiver...")

    def on_share_url_received(self, url):
        self.share_url_display.setText(url)

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

    def on_job_complete(self):
        if self.current_job and self.current_job["store"]:
            self.status_label.setText("Uploaded! Share the URL or token above.")
        else:
            self.status_label.setText("File sent! The code is still valid for more receivers.")
        self._finish_job("success")
        if not self.jobs:
            self.current_job = None

    def on_job_error(self, error):
        self.status_label.setText(f"Error: {error}")
        self._finish_job("failed")
        dialogs.show_error(self, error, "Transfer Error")

    def cancel_send(self):
        self.pirate_service.cancel()
        self.jobs.clear()
        self.current_job = None
        self.status_label.setText("Transfer cancelled.")
        self.progress_bar.setVisible(False)
        self.stats_label.setText("")
        self._set_busy(False)
        self.refresh_queue()

    # ---- clipboard ----------------------------------------------------
    def _copy(self, text, button):
        if not text:
            return
        QApplication.clipboard().setText(text)
        original = button.text()
        button.setText("Copied!")
        QTimer.singleShot(1500, lambda: button.setText(original))

    def copy_share_code(self):
        self._copy(self.share_code_display.text(), self.copy_btn)

    def copy_share_url(self):
        self._copy(self.share_url_display.text(), self.copy_url_btn)

    def closeEvent(self, event):
        self.pirate_service.cancel()
        event.accept()
