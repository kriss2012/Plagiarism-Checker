"""Native PySide6 vector-rendered charts and gauges for plagiarism analytics.
High-DPI crisp rendering dynamically optimized for professional desktop themes.
"""

from typing import Dict, List, Tuple
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class SimilarityGaugeWidget(QWidget):
    """High-DPI semi-circular speedometer gauge displaying similarity percentage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self.setMinimumSize(200, 145)

    def set_value(self, value: float):
        self._value = max(0.0, min(100.0, float(value)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height * 1.7)

        cx = width / 2.0
        cy = height - 16.0
        radius = side * 0.40

        # Track background
        pen_track = QPen(QColor("#CBD5E1"), 12, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_track)
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.drawArc(rect, 0 * 16, 180 * 16)

        # Active value arc
        val_angle = (self._value / 100.0) * 180.0

        if self._value <= 10.0:
            arc_color = QColor("#10B981")  # Emerald (Cleared)
        elif self._value <= 40.0:
            arc_color = QColor("#F59E0B")  # Amber (Minor revisions)
        elif self._value <= 60.0:
            arc_color = QColor("#EF4444")  # Red (Major revisions)
        else:
            arc_color = QColor("#991B1B")  # Crimson (Rejected)

        if self._value > 0:
            pen_val = QPen(arc_color, 12, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen_val)
            painter.drawArc(rect, 180 * 16, int(-val_angle * 16))

        # Center Value Text - High contrast dark navy
        painter.setPen(QColor("#002461"))
        font = QFont("Segoe UI", 22, QFont.Bold)
        painter.setFont(font)
        text_val = f"{self._value:.1f}%"
        painter.drawText(QRectF(cx - 75, cy - 46, 150, 30), Qt.AlignCenter, text_val)

        # Subtitle
        painter.setPen(QColor("#64748B"))
        font_sub = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font_sub)
        painter.drawText(QRectF(cx - 75, cy - 16, 150, 16), Qt.AlignCenter, "SIMILARITY INDEX")

        # Range labels
        font_lbl = QFont("Segoe UI", 7.5)
        painter.setFont(font_lbl)
        painter.drawText(int(cx - radius - 12), int(cy + 12), "0%")
        painter.drawText(int(cx + radius - 6), int(cy + 12), "100%")


class RiskDistributionWidget(QWidget):
    """Segmented horizontal bar visualizing UGC risk breakdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._distribution = {"Very Low": 0, "Low": 0, "Moderate": 0, "High": 0, "Very High": 0}
        self.setMinimumSize(240, 75)

    def set_data(self, distribution: Dict[str, int]):
        self._distribution = distribution
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        total = sum(self._distribution.values())
        if total == 0:
            painter.setPen(QColor("#64748B"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No verification records yet")
            return

        bar_y = 12
        bar_h = 16
        cur_x = 10
        avail_w = width - 20

        colors_map = [
            ("Very Low", QColor("#10B981")),
            ("Low", QColor("#3B82F6")),
            ("Moderate", QColor("#F59E0B")),
            ("High", QColor("#EF4444")),
            ("Very High", QColor("#991B1B")),
        ]

        painter.setPen(Qt.NoPen)
        for label, col in colors_map:
            cnt = self._distribution.get(label, 0)
            if cnt > 0:
                seg_w = max(4, (cnt / total) * avail_w)
                painter.setBrush(QBrush(col))
                painter.drawRoundedRect(QRectF(cur_x, bar_y, seg_w, bar_h), 4, 4)
                cur_x += seg_w + 2

        # Legend below
        leg_y = bar_y + bar_h + 14
        leg_x = 10
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        for label, col in colors_map:
            cnt = self._distribution.get(label, 0)
            painter.setBrush(QBrush(col))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(leg_x, leg_y + 2, 8, 8)

            painter.setPen(QColor("#475569"))
            lbl_text = f"{label} ({cnt})"
            painter.drawText(leg_x + 12, leg_y + 10, lbl_text)
            leg_x += len(lbl_text) * 7 + 14
            if leg_x > width - 50:
                break


class TimelineBarChartWidget(QWidget):
    """Bar chart displaying recent dissertation similarity scores."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: List[Tuple[str, float]] = []
        self.setMinimumSize(280, 145)

    def set_data(self, values: List[Tuple[str, float]]):
        self._values = values[-8:]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()

        if not self._values:
            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 9.5))
            painter.drawText(self.rect(), Qt.AlignCenter, "No verification history recorded yet")
            return

        margin_left = 35
        margin_bottom = 28
        chart_w = w - margin_left - 15
        chart_h = h - margin_bottom - 20

        # Grid lines for 0%, 50%, 100%
        painter.setPen(QPen(QColor("#E2E8F0"), 1, Qt.DashLine))
        painter.setFont(QFont("Segoe UI", 7.5))
        for pct, y_offset in [(0, chart_h), (50, chart_h / 2), (100, 0)]:
            y = 18 + y_offset
            painter.drawLine(margin_left, int(y), int(w - 15), int(y))
            painter.setPen(QColor("#64748B"))
            painter.drawText(5, int(y + 4), f"{pct}%")
            painter.setPen(QPen(QColor("#E2E8F0"), 1, Qt.DashLine))

        # Bars
        bar_count = len(self._values)
        bar_w = min(28, max(12, int(chart_w / (bar_count * 1.8))))
        spacing = (chart_w - (bar_w * bar_count)) / (bar_count + 1)

        for i, (name, sim) in enumerate(self._values):
            x = margin_left + spacing + i * (bar_w + spacing)
            bar_height = (sim / 100.0) * chart_h
            y = 18 + chart_h - bar_height

            if sim <= 10:
                bar_color = QColor("#10B981")
            elif sim <= 40:
                bar_color = QColor("#F59E0B")
            else:
                bar_color = QColor("#EF4444")

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bar_color))
            painter.drawRoundedRect(QRectF(x, y, bar_w, bar_height), 4, 4)

            painter.setPen(QColor("#475569"))
            short_name = name[:5] + ".." if len(name) > 6 else name
            painter.drawText(QRectF(x - 10, h - margin_bottom + 5, bar_w + 20, 18), Qt.AlignCenter, short_name)
