"""Application entry point for ResearchGuard desktop application.
Initializes logging, SQLite database, Qt application lifecycle, and primary window.
Shows an animated splash screen on launch with KiriGen Tech watermark.
"""

import sys
import traceback
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from app.config import APP_TITLE
from app.database.session import init_db
from app.ui.main_window import MainWindow
from app.ui.splash import AnimatedSplash
from app.utils.logger import logger


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Logs unhandled exceptions and displays a user-friendly modal dialog."""
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Unhandled Application Exception:\n{err_msg}")

    # Avoid showing dialog if application is closing
    if QApplication.instance():
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Unexpected Application Error")
        msg_box.setText("An unexpected error occurred during execution.")
        msg_box.setInformativeText(f"{exc_type.__name__}: {exc_value}")
        msg_box.setDetailedText(err_msg)
        msg_box.exec()


def main():
    """Main execution function."""
    sys.excepthook = handle_uncaught_exception

    logger.info("==================================================")
    logger.info(f"Starting {APP_TITLE}")
    logger.info(f"Python: {sys.version}")
    logger.info("==================================================")

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ResearchGuard")
    app.setOrganizationName("IMRD Shirpur")

    # Set Application Icon
    from pathlib import Path
    from PySide6.QtGui import QIcon
    icon_path = Path(__file__).resolve().parent.parent / "resources" / "app_icon.png"
    if not icon_path.exists():
        icon_path = Path(__file__).resolve().parent.parent / "Logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # ── Animated Splash Screen ─────────────────────────────────────────
    splash = AnimatedSplash()
    splash.show()
    app.processEvents()  # ensure splash paints before blocking DB init

    # Initialise DB while splash is visible (runs synchronously but
    # the splash animation is timer-driven so it continues to paint).
    db_error = None
    try:
        init_db()
        logger.info("Database initialised successfully.")
    except Exception as e:
        logger.error(f"Database initialization failure: {e}", exc_info=True)
        db_error = e

    # Keep a reference; created now, shown only after splash closes
    window_holder = {}

    def _launch_main():
        """Called when the splash animation finishes."""
        if db_error:
            QMessageBox.critical(
                None, "Database Error",
                f"Failed to initialize local database:\n{db_error}"
            )
            app.quit()
            return

        try:
            window = MainWindow()
            window_holder["w"] = window   # keep reference alive
            window.show()
        except Exception as e:
            logger.error(f"Failed to show main window: {e}", exc_info=True)
            QMessageBox.critical(None, "Startup Error", f"Could not launch application window:\n{e}")
            app.quit()

    splash.finished.connect(_launch_main)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
