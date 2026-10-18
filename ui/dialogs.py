"""Consistent styled message dialogs for PirateDrop."""

from PySide6.QtWidgets import QMessageBox


def _show(parent, icon, title, text, buttons=QMessageBox.Ok):
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(buttons)
    return box.exec()


def show_error(parent, text, title="Error"):
    return _show(parent, QMessageBox.Critical, title, text)


def show_warning(parent, text, title="Warning"):
    return _show(parent, QMessageBox.Warning, title, text)


def show_info(parent, text, title="Information"):
    return _show(parent, QMessageBox.Information, title, text)


def ask_confirm(parent, text, title="Confirm"):
    result = _show(parent, QMessageBox.Question, title, text, QMessageBox.Yes | QMessageBox.No)
    return result == QMessageBox.Yes
