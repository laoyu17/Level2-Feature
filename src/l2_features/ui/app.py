from __future__ import annotations

import sys


def run_ui() -> None:
    try:
        from PyQt6.QtWidgets import QApplication
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyQt6 is not installed. Run: pip install -e .[ui]") from exc

    from l2_features.ui.windows.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
