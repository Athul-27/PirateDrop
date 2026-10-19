"""Minimal black-and-white transfer-speed sparkline drawn with QPainter."""

import time
from collections import deque

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen

MAX_POINTS = 180


class SpeedSparkline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(84)
        self.setMaximumHeight(96)
        self._samples = deque(maxlen=MAX_POINTS)

    def add_sample(self, speed_mb_s, at=None):
        if speed_mb_s is None or speed_mb_s < 0:
            return
        self._samples.append((at if at is not None else time.monotonic(), float(speed_mb_s)))
        self.update()

    def clear_data(self):
        self._samples.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawRect(rect.adjusted(1, 1, -2, -2))

        if len(self._samples) < 2:
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.drawText(rect, Qt.AlignCenter, "collecting speed data...")
            painter.end()
            return

        samples = list(self._samples)
        t0, t1 = samples[0][0], samples[-1][0]
        span = max(t1 - t0, 1e-6)
        peak = max(value for _, value in samples) or 1.0
        inner = rect.adjusted(10, 12, -10, -10)

        points = []
        for timestamp, value in samples:
            x = inner.left() + (timestamp - t0) / span * inner.width()
            y = inner.bottom() - (value / peak) * inner.height()
            points.append(QPointF(x, y))

        painter.setPen(QPen(QColor("#000000"), 2))
        for index in range(1, len(points)):
            painter.drawLine(points[index - 1], points[index])

        painter.setPen(QPen(QColor("#000000"), 1))
        painter.drawText(inner, Qt.AlignTop | Qt.AlignRight, f"peak {peak:.1f} MB/s")
        painter.end()
