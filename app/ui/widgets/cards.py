"""Dashboard KPI metric cards and status badges for IMRD ResearchGuard."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class MetricCard(QFrame):
    """Reusable desktop metric card adapted for both light and dark themes."""

    def __init__(self, title: str, initial_value: str = "-", subtitle: str = "", accent_color: str = "#005FEA", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(95)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(3)

        # Title
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #475569; font-size: 10.5px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(self.title_label)

        # Value
        self.val_label = QLabel(initial_value)
        self.val_label.setStyleSheet(f"color: {accent_color}; font-size: 24px; font-weight: 800; line-height: 1.1;")
        layout.addWidget(self.val_label)

        # Subtitle
        self.sub_label = QLabel(subtitle)
        self.sub_label.setStyleSheet("color: #64748B; font-size: 11px;")
        layout.addWidget(self.sub_label)

    def set_value(self, value: str, subtitle: str = ""):
        self.val_label.setText(str(value))
        if subtitle:
            self.sub_label.setText(subtitle)


class RiskBadge(QLabel):
    """Colored pill badge displaying academic risk level or UGC status."""

    def __init__(self, risk_level: str = "Very Low", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_level(risk_level)

    def set_level(self, risk_level: str):
        self.setText(risk_level.upper())
        level = risk_level.lower()

        if "very low" in level or "approved" in level:
            bg, fg, border = "#ECFDF5", "#047857", "#10B981"
        elif "low" in level:
            bg, fg, border = "#EFF6FF", "#1D4ED8", "#3B82F6"
        elif "moderate" in level or "revision" in level:
            bg, fg, border = "#FFFBEB", "#B45309", "#F59E0B"
        elif "very high" in level or "rejected" in level:
            bg, fg, border = "#450A0A", "#FFFFFF", "#991B1B"
        else:  # High
            bg, fg, border = "#FEF2F2", "#B91C1C", "#EF4444"

        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 10.5px;
            font-weight: 700;
        """)
