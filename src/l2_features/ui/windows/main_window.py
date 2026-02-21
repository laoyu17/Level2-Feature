from __future__ import annotations

from pathlib import Path

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QComboBox,
        QFileDialog,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyQt6 is required for UI components") from exc

from l2_features.ui.viewmodels.replay_viewmodel import ReplayViewModel
from l2_features.ui.widgets.feature_plot import FeaturePlotWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("L2 Features Workbench")
        self.resize(1280, 820)

        self._vm = ReplayViewModel(self)
        self._vm.data_loaded.connect(self._on_data_loaded)
        self._vm.frame_changed.connect(self._on_frame)
        self._vm.stats_changed.connect(self.statusBar().showMessage)

        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        container = QWidget()
        root = QVBoxLayout(container)

        io_box = QGroupBox("Data Source")
        io_layout = QHBoxLayout(io_box)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select csv/parquet file")
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("symbol (optional)")

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._select_file)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._load_data)

        io_layout.addWidget(QLabel("File"))
        io_layout.addWidget(self.path_input, stretch=4)
        io_layout.addWidget(browse_btn)
        io_layout.addWidget(QLabel("Symbol"))
        io_layout.addWidget(self.symbol_input, stretch=1)
        io_layout.addWidget(load_btn)

        control_box = QGroupBox("Replay")
        control_layout = QHBoxLayout(control_box)
        play_btn = QPushButton("Play")
        pause_btn = QPushButton("Pause")
        stop_btn = QPushButton("Stop")
        speed_half = QPushButton("0.5x")
        speed_one = QPushButton("1x")
        speed_two = QPushButton("2x")
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["batch-playback", "stream-playback"])
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)

        play_btn.clicked.connect(self._vm.play)
        pause_btn.clicked.connect(self._vm.pause)
        stop_btn.clicked.connect(self._vm.stop)
        speed_half.clicked.connect(lambda: self._vm.set_speed(0.5))
        speed_one.clicked.connect(lambda: self._vm.set_speed(1.0))
        speed_two.clicked.connect(lambda: self._vm.set_speed(2.0))

        for w in [play_btn, pause_btn, stop_btn, speed_half, speed_one, speed_two]:
            control_layout.addWidget(w)
        control_layout.addWidget(QLabel("Mode"))
        control_layout.addWidget(self.mode_selector)
        control_layout.addStretch()

        content = QWidget()
        content_layout = QGridLayout(content)

        self.book_table = QTableWidget(10, 4)
        self.book_table.setHorizontalHeaderLabels(["BidPx", "BidSz", "AskPx", "AskSz"])
        self.book_table.verticalHeader().setVisible(False)
        self.book_table.setAlternatingRowColors(True)

        self.feature_plot = FeaturePlotWidget(self)

        content_layout.addWidget(self._wrap_panel("Order Book", self.book_table), 0, 0)
        content_layout.addWidget(self._wrap_panel("Features", self.feature_plot), 0, 1)
        content_layout.setColumnStretch(0, 1)
        content_layout.setColumnStretch(1, 2)

        root.addWidget(io_box)
        root.addWidget(control_box)
        root.addWidget(content)

        self.setCentralWidget(container)

    def _wrap_panel(self, title: str, widget: QWidget) -> QWidget:
        panel = QGroupBox(title)
        layout = QVBoxLayout(panel)
        layout.addWidget(widget)
        return panel

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f7f9fb; }
            QGroupBox {
                border: 1px solid #d8dee9;
                border-radius: 8px;
                margin-top: 10px;
                font-weight: 600;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QPushButton {
                background: #2f6feb;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background: #1f5cc9; }
            QLineEdit { padding: 6px; border: 1px solid #d0d7de; border-radius: 6px; }
            """
        )

    def _select_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Level2 File",
            "",
            "Data Files (*.csv *.parquet)",
        )
        if path:
            self.path_input.setText(path)

    def _load_data(self) -> None:
        raw_path = self.path_input.text().strip()
        if not raw_path:
            QMessageBox.warning(self, "Warning", "Please select a file first")
            return

        path = Path(raw_path)
        symbol = self.symbol_input.text().strip() or None
        try:
            self._vm.load_file(path, symbol=symbol)
        except Exception as exc:  # pragma: no cover
            QMessageBox.critical(self, "Load failed", str(exc))

    def _on_data_loaded(self, rows: int) -> None:
        self.statusBar().showMessage(f"Loaded {rows} frames ({self._vm.mode})")

    def _on_frame(self, frame: dict) -> None:
        self._update_book_table(frame)
        self.feature_plot.update_history(self._vm.history)

    def _on_mode_changed(self, mode: str) -> None:
        try:
            self._vm.set_mode(mode)
        except Exception as exc:  # pragma: no cover
            QMessageBox.warning(self, "Replay mode", str(exc))

    def _update_book_table(self, frame: dict) -> None:
        for i in range(1, 11):
            bid_px = frame.get(f"bid_px_{i}", 0.0)
            bid_sz = frame.get(f"bid_sz_{i}", 0.0)
            ask_px = frame.get(f"ask_px_{i}", 0.0)
            ask_sz = frame.get(f"ask_sz_{i}", 0.0)

            values = [bid_px, bid_sz, ask_px, ask_sz]
            for col, value in enumerate(values):
                text = f"{value:.6f}" if isinstance(value, float) else str(value)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.book_table.setItem(i - 1, col, item)
