"""Native PySide6 vector-rendered charts and gauges for plagiarism analytics.
High-DPI crisp rendering without bulky external plotting dependencies.
"""

import math
from typing import Dict, List, Tuple
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class SimilarityGaugeWidget(QWidget):
    """High-DPI semi-circular speedometer gauge for displaying overall similarity percentage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0  # 0.0 to 100.0%
        self.setMinimumSize(220, 160)

    def set_value(self, value: float):
        self._value = max(0.0, min(100.0, float(value)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height * 1.8)

        # Center point and radius
        cx = width / 2.0
        cy = height - 25.0
        radius = side * 0.42

        # Draw background track
        pen_track = QPen(QColor("#334155"), 14, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_track)
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        # 180 degrees arc: from 180 (left) to 0 (right) in Qt 16ths of a degree
        painter.drawArc(rect, 0 * 16, 180 * 16)

        # Draw active value arc with gradient color
        val_angle = (self._value / 100.0) * 180.0

        # Determine color based on risk
        if self._value <= 10.0:
            arc_color = QColor("#10B981")  # Emerald Green
        elif self._value <= 25.0:
            arc_color = QColor("#3B82F6")  # Blue
        elif self._value <= 40.0:
            arc_color = QColor("#F59E0B")  # Amber
        elif self._value <= 60.0:
            arc_color = QColor("#EF4444")  # Red
        else:
            arc_color = QColor("#991B1B")  # Deep Crimson

        if self._value > 0:
            pen_val = QPen(arc_color, 14, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen_val)
            # In Qt, 180 is left, angle spans counter-clockwise if negative
            painter.drawArc(rect, 180 * 16, int(-val_angle * 16))

        # Draw Center Value Text
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", 24, QFont.Bold)
        painter.setFont(font)
        text_val = f"{self._value:.1f}%"
        painter.drawText(QRectF(cx - 80, cy - 50, 160, 36), Qt.AlignCenter, text_val)

        # Label: SIMILARITY
        painter.setPen(QColor("#94A3B8"))
        font_sub = QFont("Segoe UI", 9, QFont.DemiBold)
        painter.setFont(font_sub)
        painter.drawText(QRectF(cx - 80, cy - 14, 160, 20), Qt.AlignCenter, "SIMILARITY INDEX")

        # Range labels: 0% and 100%
        font_lbl = QFont("Segoe UI", 8)
        painter.setFont(font_lbl)
        painter.drawText(int(cx - radius - 15), int(cy + 16), "0%")
        painter.drawText(int(cx + radius - 5), int(cy + 16), "100%")


class RiskDistributionWidget(QWidget):
    """Segmented horizontal bar visualizing risk level breakdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._distribution = {"Very Low": 0, "Low": 0, "Moderate": 0, "High": 0, "Very High": 0}
        self.setMinimumSize(250, 80)

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
            painter.drawText(self.rect(), Qt.AlignCenter, "No documents analyzed yet")
            return

        bar_y = 15
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

        # Draw Legend below
        leg_y = bar_y + bar_h + 16
        leg_x = 10
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        for label, col in colors_map:
            cnt = self._distribution.get(label, 0)
            painter.setBrush(QBrush(col))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(leg_x, leg_y + 2, 8, 8)

            painter.setPen(QColor("#94A3B8"))
            lbl_text = f"{label} ({cnt})"
            painter.drawText(leg_x + 12, leg_y + 10, lbl_text)
            leg_x += len(lbl_text) * 7 + 16
            if leg_x > width - 60:
                break


class TimelineBarChartWidget(QWidget):
    """Bar chart displaying recent similarity scores."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: List[Tuple[str, float]] = []  # List of (doc_name, similarity)
        self.setMinimumSize(300, 150)

    def set_data(self, values: List[Tuple[str, float]]):
        self._values = values[-8:]  # Show last 8 documents
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if not self._values:
            painter.setPen(QColor("#64748B"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No check history recorded yet")
            return

        margin_left = 35
        margin_bottom = 30
        chart_w = w - margin_left - 15
        chart_h = h - margin_bottom - 20

        # Draw grid lines for 0%, 50%, 100%
        painter.setPen(QPen(QColor("#334155"), 1, Qt.DashLine))
        painter.setFont(QFont("Segoe UI", 7))
        for pct, y_offset in [(0, chart_h), (50, chart_h / 2), (100, 0)]:
            y = 20 + y_offset
            painter.drawLine(margin_left, int(y), int(w - 15), int(y))
            painter.setPen(QColor("#64748B"))
            painter.drawText(5, int(y + 4), f"{pct}%")
            painter.setPen(QPen(QColor("#334155"), 1, Qt.DashLine))

        # Draw Bars
        bar_count = len(self._values)
        bar_w = min(28, max(12, int(chart_w / (bar_count * 1.8))))
        spacing = (chart_w - (bar_w * bar_count)) / (bar_count + 1)

        for i, (name, sim) in enumerate(self._values):
            x = margin_left + spacing + i * (bar_w + spacing)
            bar_height = (sim / 100.0) * chart_h
            y = 20 + chart_h - bar_height

            # Color by similarity
            if sim <= 10:
                bar_color = QColor("#10B981")
            elif sim <= 25:
                bar_color = QColor("#3B82F6")
            elif sim <= 40:
                bar_color = QColor("#F59E0B")
            else:
                bar_color = QColor("#EF4444")

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bar_color))
            painter.drawRoundedRect(QRectF(x, y, bar_w, bar_height), 4, 4)

            # Label on bottom
            painter.setPen(QColor("#94A3B8"))
            short_name = name[:5] + ".." if len(name) > 6 else name
            painter.drawText(QRectF(x - 10, h - margin_bottom + 5, bar_w + 20, 20), Qt.AlignCenter, short_name)
