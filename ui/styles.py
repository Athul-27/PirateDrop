# Neo-Brutalist Qt Style Sheets for PirateDrop

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QFont
from PySide6.QtCore import Qt

GLOBAL_STYLESHEET = """
QWidget {
    background-color: #FFFFFF;
    color: #000000;
}

QLabel {
    background-color: transparent;
    color: #000000;
    font-size: 13px;
}

/* Header */
QFrame#header {
    background-color: #000000;
    border-bottom: 3px solid #000000;
}
QFrame#header QLabel {
    background-color: transparent;
}
QLabel#headerTitle {
    color: #FFFFFF;
    font-size: 32px;
    font-weight: bold;
    letter-spacing: 6px;
}
QLabel#headerSubtitle {
    color: #FFFFFF;
    font-size: 11px;
    letter-spacing: 3px;
}

/* Navigation */
QFrame#nav {
    background-color: #FFFFFF;
    border-bottom: 3px solid #000000;
}

QLabel#sectionLabel {
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
}

QLabel#statsLabel {
    color: #000000;
    font-size: 12px;
}

QPushButton {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 0px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #000000;
    color: #FFFFFF;
}
QPushButton:pressed {
    background-color: #000000;
    color: #FFFFFF;
}
QPushButton:disabled {
    background-color: #E0E0E0;
    color: #808080;
    border: 2px solid #808080;
}

QPushButton#navButton {
    background-color: #FFFFFF;
    color: #000000;
    border: none;
    border-right: 2px solid #000000;
    border-radius: 0px;
    padding: 12px 26px;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 2px;
    min-width: 110px;
}
QFrame#nav QPushButton#navButton:first {
    border-left: 3px solid #000000;
}
QPushButton#navButton:hover {
    background-color: #F0F0F0;
    color: #000000;
}
QPushButton#navButton:checked {
    background-color: #000000;
    color: #FFFFFF;
}

QPushButton#primaryButton {
    background-color: #000000;
    color: #FFFFFF;
    border: 2px solid #000000;
    border-radius: 0px;
    padding: 14px 24px;
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 2px;
}
QPushButton#primaryButton:hover {
    background-color: #FFFFFF;
    color: #000000;
}
QPushButton#primaryButton:pressed {
    background-color: #FFFFFF;
    color: #000000;
}
QPushButton#primaryButton:disabled {
    background-color: #E0E0E0;
    color: #808080;
    border: 2px solid #808080;
}

/* Inputs */
QLineEdit {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 0px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #000000;
    selection-color: #FFFFFF;
}
QLineEdit:focus {
    border: 2px solid #000000;
}
QLineEdit:read-only {
    background-color: #F5F5F5;
}
QLineEdit:disabled {
    background-color: #EFEFEF;
    color: #808080;
}
QLineEdit#shareCode {
    font-family: "Courier New", monospace;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLineEdit#shareUrl {
    font-family: "Courier New", monospace;
    font-size: 12px;
}

QComboBox, QSpinBox {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 0px;
    padding: 6px 10px;
    font-size: 13px;
}
QComboBox:disabled, QSpinBox:disabled {
    background-color: #EFEFEF;
    color: #808080;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border-left: 2px solid #000000;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #000000;
    selection-background-color: #000000;
    selection-color: #FFFFFF;
    outline: none;
}

QCheckBox {
    background-color: transparent;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #000000;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #000000;
}

/* Lists */
QListWidget {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 0px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #E0E0E0;
}
QListWidget::item:selected {
    background-color: #000000;
    color: #FFFFFF;
}
QListWidget::item:hover {
    background-color: #F0F0F0;
    color: #000000;
}

/* Panels */
QGroupBox, QFrame#panel {
    border: 2px solid #000000;
    border-radius: 0px;
    background-color: #FFFFFF;
}
QGroupBox {
    margin-top: 14px;
    padding-top: 18px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    background-color: #FFFFFF;
}

/* Progress */
QProgressBar {
    border: 2px solid #000000;
    border-radius: 0px;
    background-color: #FFFFFF;
    text-align: center;
    height: 22px;
    font-weight: bold;
    color: #000000;
}
QProgressBar::chunk {
    background-color: #000000;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #FFFFFF;
    width: 12px;
    border-left: 2px solid #000000;
}
QScrollBar::handle:vertical {
    background-color: #000000;
    min-height: 30px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #FFFFFF;
    height: 12px;
    border-top: 2px solid #000000;
}
QScrollBar::handle:horizontal {
    background-color: #000000;
    min-width: 30px;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Dialogs */
QMessageBox {
    background-color: #FFFFFF;
}
QMessageBox QLabel {
    color: #000000;
    font-size: 13px;
}
QMessageBox QPushButton {
    min-width: 80px;
}

QToolTip {
    background-color: #000000;
    color: #FFFFFF;
    border: 2px solid #000000;
    padding: 4px 8px;
}
"""


def apply_styles(app: QApplication):
    app.setStyleSheet(GLOBAL_STYLESHEET)

    palette = QPalette()
    palette.setColor(QPalette.Window, Qt.white)
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.AlternateBase, Qt.white)
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, Qt.white)
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.Highlight, Qt.black)
    palette.setColor(QPalette.HighlightedText, Qt.white)
    palette.setColor(QPalette.PlaceholderText, Qt.black)
    app.setPalette(palette)

    app.setFont(QFont("Segoe UI", 10))
