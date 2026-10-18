from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QGroupBox,
)
from PySide6.QtCore import Qt

from services.pirate_service import PirateService
from services.config import get_config, resolve_croc_path
from ui import dialogs


class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(400)
        self.config = get_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # --- croc executable ---
        exec_group = QGroupBox("Croc Executable")
        exec_layout = QVBoxLayout()
        exec_layout.setSpacing(8)

        exec_row = QHBoxLayout()
        self.exec_path_display = QLineEdit()
        self.exec_path_display.setReadOnly(True)
        self.exec_browse_btn = QPushButton("Browse")
        self.exec_browse_btn.clicked.connect(self.browse_executable)
        exec_row.addWidget(self.exec_path_display, 1)
        exec_row.addWidget(self.exec_browse_btn)
        exec_layout.addLayout(exec_row)

        self.version_label = QLabel("Version: unknown")
        exec_layout.addWidget(self.version_label)

        self.test_conn_btn = QPushButton("Test Connection")
        self.test_conn_btn.clicked.connect(self.test_croc_connection)
        exec_layout.addWidget(self.test_conn_btn)

        exec_group.setLayout(exec_layout)
        layout.addWidget(exec_group)

        # --- default settings ---
        settings_group = QGroupBox("Default Settings")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(8)

        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel("Default Destination:"))
        self.default_dest_input = QLineEdit()
        self.default_dest_input.setPlaceholderText("Select default destination folder...")
        self.default_dest_input.setReadOnly(True)
        self.dest_browse_btn = QPushButton("Browse")
        self.dest_browse_btn.clicked.connect(self.browse_default_destination)
        dest_row.addWidget(self.default_dest_input, 1)
        dest_row.addWidget(self.dest_browse_btn)
        settings_layout.addLayout(dest_row)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # --- buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self.apply_settings)
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)
        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)
        self.load_settings()

    # ---- data ---------------------------------------------------------
    def load_settings(self):
        self.exec_path_display.setText(resolve_croc_path())
        self.default_dest_input.setText(self.config.get("default_destination") or "")

    def browse_executable(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Croc Executable", "", "Executable Files (*.exe);;All Files (*)"
        )
        if file:
            self.exec_path_display.setText(file)

    def browse_default_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Default Destination Folder")
        if folder:
            self.default_dest_input.setText(folder)

    def test_croc_connection(self):
        service = PirateService(self.exec_path_display.text().strip())
        ok, info = service.is_available()
        if ok:
            self.version_label.setText(f"Version: {info}")
            dialogs.show_info(self, f"croc is available.\n\n{info}", "Connection OK")
        else:
            self.version_label.setText("Version: unknown")
            dialogs.show_warning(self, f"Could not run croc.\n\n{info}", "Connection Failed")

    def apply_settings(self):
        self.config.update(
            croc_path=self.exec_path_display.text().strip(),
            default_destination=self.default_dest_input.text().strip(),
        )
        dialogs.show_info(self, "Settings saved.", "Settings Applied")

    def reset_settings(self):
        self.config.update(croc_path="", default_destination="")
        self.default_dest_input.setText("")
        self.exec_path_display.setText(resolve_croc_path())
        self.version_label.setText("Version: unknown")
        dialogs.show_info(self, "Settings reset to default values.", "Settings Reset")
