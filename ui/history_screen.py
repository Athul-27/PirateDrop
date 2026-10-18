from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
)

from services.history import get_history
from ui import dialogs


class HistoryScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.history = get_history()
        self.init_ui()
        self.refresh()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Transfer History")
        title.setObjectName("sectionLabel")
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self.clear_history)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.clear_btn)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def _describe(self, entry):
        when = entry.get("time", "")
        direction = entry.get("direction", "")
        items = entry.get("items", [])
        count = entry.get("count", len(items))
        preview = ", ".join(items[:3])
        if count > 3:
            preview += f" (+{count - 3} more)"
        code = entry.get("code", "")
        outcome = entry.get("outcome", "")
        suffix = f"  [{outcome}]" if outcome and outcome != "success" else ""
        return f"{when}   {direction.upper():<8} {preview}{suffix}\n    code: {code}"

    def refresh(self):
        self.list_widget.clear()
        entries = self.history.entries
        if not entries:
            self.status_label.setText("No transfers yet.")
            return
        for entry in entries:
            self.list_widget.addItem(self._describe(entry))
        self.status_label.setText(f"{len(entries)} entr(y/ies).")

    def clear_history(self):
        if dialogs.ask_confirm(self, "Clear all transfer history?", "Clear History"):
            self.history.clear()
            self.refresh()
