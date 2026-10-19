import base64
import os

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.send_screen import SendScreen
from ui.receive_screen import ReceiveScreen
from ui.settings_screen import SettingsScreen
from ui.history_screen import HistoryScreen
from services.config import bundled_dir, get_config

APP_TITLE = "PirateDrop"


class PirateDropUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(820, 680)
        self.resize(900, 760)
        self.init_ui()
        self._restore_geometry()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self.build_header())
        root.addWidget(self.build_navigation())

        self.stacked_widget = QStackedWidget()
        self.send_screen = SendScreen()
        self.receive_screen = ReceiveScreen()
        self.history_screen = HistoryScreen()
        self.settings_screen = SettingsScreen()
        self.stacked_widget.addWidget(self.send_screen)
        self.stacked_widget.addWidget(self.receive_screen)
        self.stacked_widget.addWidget(self.history_screen)
        self.stacked_widget.addWidget(self.settings_screen)
        root.addWidget(self.stacked_widget)

        self.switch_page(0)

    def build_header(self):
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(12)

        icon_label = QLabel()
        icon_label.setObjectName("headerIcon")
        icon_path = os.path.join(bundled_dir(), "assets", "icon.ico")
        if os.path.isfile(icon_path):
            icon_label.setPixmap(QIcon(icon_path).pixmap(48, 48))
        icon_label.setFixedWidth(48)

        title = QLabel(APP_TITLE)
        title.setObjectName("headerTitle")

        layout.addStretch(1)
        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addStretch(1)
        return header

    def build_navigation(self):
        nav = QFrame()
        nav.setObjectName("nav")
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav_buttons = []
        for index, label in enumerate(["SEND", "RECEIVE", "HISTORY", "SETTINGS"]):
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=index: self.switch_page(i))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()
        return nav

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if self.stacked_widget.currentWidget() is self.history_screen:
            self.history_screen.refresh()

    def _restore_geometry(self):
        raw = get_config().get("window_geometry")
        if raw:
            try:
                self.restoreGeometry(base64.b64decode(raw))
            except Exception:
                pass

    def closeEvent(self, event):
        try:
            get_config().update(
                window_geometry=base64.b64encode(bytes(self.saveGeometry())).decode()
            )
        except Exception:
            pass
        for screen in (self.send_screen, self.receive_screen):
            try:
                screen.pirate_service.cancel()
            except Exception:
                pass
        event.accept()
