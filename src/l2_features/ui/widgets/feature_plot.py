from __future__ import annotations

from collections.abc import Mapping, Sequence

try:
    import pyqtgraph as pg
    from PyQt6.QtWidgets import QLabel, QStackedLayout, QWidget
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyQt6 + pyqtgraph are required for FeaturePlotWidget") from exc


class FeaturePlotWidget(QWidget):
    """显示 3 条核心特征时序曲线。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QStackedLayout(self)

        self._plot = pg.PlotWidget()
        self._plot.showGrid(x=True, y=True)
        self._plot.setTitle("Feature Panel")
        self._plot.addLegend()

        self._curves = {
            "obi_l1": self._plot.plot(name="obi_l1", pen=pg.mkPen("#3498db", width=2)),
            "spread_abs": self._plot.plot(name="spread_abs", pen=pg.mkPen("#e67e22", width=2)),
            "instant_impact": self._plot.plot(
                name="instant_impact",
                pen=pg.mkPen("#2ecc71", width=2),
            ),
        }

        self._empty = QLabel("Load data to start replay")
        self._layout.addWidget(self._empty)
        self._layout.addWidget(self._plot)
        self._layout.setCurrentWidget(self._empty)

    def update_history(self, history: Mapping[str, Sequence[float]]) -> None:
        x_axis = range(len(next(iter(history.values()), [])))
        has_data = False
        for name, curve in self._curves.items():
            values = list(history.get(name, []))
            if values:
                has_data = True
            curve.setData(list(x_axis), values)

        if has_data:
            self._layout.setCurrentWidget(self._plot)
