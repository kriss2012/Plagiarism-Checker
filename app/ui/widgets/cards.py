"""Dashboard KPI metric cards, empty states, and status badges for IMRD ResearchGuard."""

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class MetricCard(QFrame):
    """Reusable desktop metric card with standardized 3-tier architecture:
    1. LABEL (bold uppercase, 10.5px)
    2. VALUE (prominent bold accent, 22-24px)
    3. SUPPORTING TEXT (secondary, word-wrapped, 11px)
    """

    def __init__(
        self,
        title: str,
        initial_value: str = "-",
        subtitle: str = "",
        accent_color: str = "#005FEA",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)

        # 1. LABEL
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("cardLabel")
        self.title_label.setStyleSheet("color: #475569; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # 2. VALUE
        self.val_label = QLabel(initial_value)
        self.val_label.setObjectName("cardValue")
        self.val_label.setStyleSheet(f"color: {accent_color}; font-size: 22px; font-weight: 800; line-height: 1.1;")
        self.val_label.setWordWrap(True)
        layout.addWidget(self.val_label)

        # 3. SUPPORTING TEXT
        self.sub_label = QLabel(subtitle)
        self.sub_label.setObjectName("cardSubtitle")
        self.sub_label.setStyleSheet("color: #64748B; font-size: 11px;")
        self.sub_label.setWordWrap(True)
        layout.addWidget(self.sub_label)

    def set_value(self, value: str, subtitle: str = ""):
        self.val_label.setText(str(value))
        if subtitle:
            self.sub_label.setText(subtitle)


class EmptyStateWidget(QFrame):
    """Standardized, intentional empty state presentation for tables and views.
    Renders an icon, clear title, explanatory subtitle, and optional call-to-action button.
    """

    def __init__(
        self,
        title: str,
        message: str = "",
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #002461;")
        layout.addWidget(self.title_lbl)

        # Message
        if message:
            self.msg_lbl = QLabel(message)
            self.msg_lbl.setAlignment(Qt.AlignCenter)
            self.msg_lbl.setStyleSheet("font-size: 11.5px; color: #64748B; max-width: 480px;")
            self.msg_lbl.setWordWrap(True)
            layout.addWidget(self.msg_lbl)

        # Action Button
        if action_text and action_callback:
            self.action_btn = QPushButton(action_text)
            self.action_btn.setObjectName("primaryBtn")
            self.action_btn.setFixedHeight(32)
            self.action_btn.setCursor(Qt.PointingHandCursor)
            self.action_btn.clicked.connect(action_callback)
            layout.addWidget(self.action_btn, alignment=Qt.AlignCenter)


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
            padding: 3px 8px;
            font-size: 10.5px;
            font-weight: 700;
        """)

