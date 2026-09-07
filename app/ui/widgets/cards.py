"""Dashboard KPI metric cards and status badges."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class MetricCard(QFrame):
    """Reusable modern metric card for dashboard statistics."""

    def __init__(self, title: str, initial_value: str = "-", subtitle: str = "", accent_color: str = "#4F46E5", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(105)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        # Title
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        layout.addWidget(self.title_label)

        # Value
        self.val_label = QLabel(initial_value)
        self.val_label.setStyleSheet(f"color: {accent_color}; font-size: 26px; font-weight: 800; line-height: 1;")
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
    """Colored pill badge displaying academic risk level."""

    def __init__(self, risk_level: str = "Very Low", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_level(risk_level)

    def set_level(self, risk_level: str):
        self.setText(risk_level.upper())
        level = risk_level.lower()

        if "very low" in level:
            bg, fg, border = "rgba(16, 185, 129, 0.15)", "#10B981", "#10B981"
        elif "low" in level:
            bg, fg, border = "rgba(59, 130, 246, 0.15)", "#3B82F6", "#3B82F6"
        elif "moderate" in level:
            bg, fg, border = "rgba(245, 158, 11, 0.15)", "#F59E0B", "#F59E0B"
        elif "very high" in level:
            bg, fg, border = "rgba(153, 27, 27, 0.2)", "#F87171", "#DC2626"
        else:  # High
            bg, fg, border = "rgba(239, 68, 68, 0.15)", "#EF4444", "#EF4444"

        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 700;
        """)
