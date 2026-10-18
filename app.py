import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

from ui.main_window import PirateDropUI, APP_TITLE
from ui.styles import apply_styles
from ui import dialogs
from services.config import get_config, bundled_dir, resolve_croc_path
from services.pirate_service import PirateService


def load_icon():
    icon_path = os.path.join(bundled_dir(), "assets", "icon.ico")
    if os.path.isfile(icon_path):
        return QIcon(icon_path)
    return QIcon()


def maybe_show_security_notice(app, window):
    config = get_config()
    if not config.get("show_security_notice"):
        return
    dialogs.show_info(
        window,
        "PirateDrop wraps the croc CLI for peer-to-peer transfers.\n\n"
        "• Share codes, links and tokens only with people you trust.\n"
        "• Anyone with a code/link can download the transfer.\n"
        "• Stored transfers upload an encrypted copy to getcroc.com.\n\n"
        "Keep croc up to date for security fixes.",
        "Before you start",
    )
    config.update(show_security_notice=False)


def check_croc_available(window):
    ok, info = PirateService(resolve_croc_path()).is_available()
    if not ok:
        dialogs.show_error(
            window,
            "The croc executable could not be found or failed to run.\n\n"
            f"Details: {info}\n\n"
            "Set its location in the SETTINGS tab, or place croc.exe next to PirateDrop.",
            "croc not available",
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setApplicationDisplayName(APP_TITLE)
    app.setOrganizationName(APP_TITLE)

    apply_styles(app)

    window = PirateDropUI()
    icon = load_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
        window.setWindowIcon(icon)
    window.show()

    def startup_checks():
        maybe_show_security_notice(app, window)
        check_croc_available(window)

    QTimer.singleShot(300, startup_checks)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
