"""Animated splash screen for IMRD ResearchGuard.

Displays a professional opening animation with:
  - Background image fade-in
  - Institution branding entrance (slide + fade)
  - KiriGen Tech watermark
  - Animated loading progress bar
  - Sequential status messages
  - Auto-closes when loading completes and emits `finished` signal
"""

from pathlib import Path
from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QSequentialAnimationGroup,
    QParallelAnimationGroup,
    QRect,
    Signal,
    Property,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPixmap,
    QLinearGradient,
    QPen,
    QBrush,
)
from PySide6.QtWidgets import QSplashScreen, QApplication, QWidget, QLabel

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class AnimatedSplash(QWidget):
    """
    Full-screen animated splash window.

    Phases:
      0–400 ms   — background + logo fade in
      400–900 ms — institution title slides down from top
      900–1400ms — subtitle and accreditation fade in
      1400–3200ms— progress bar animates left→right
      3200–3600ms— all elements fade out
      3600ms     — `finished` signal emitted, window closes
    """

    finished = Signal()

    # -------------------------------------------------------------------
    # Qt property wrappers so QPropertyAnimation can drive them
    # -------------------------------------------------------------------
    def _get_bg_opacity(self):      return self._bg_opacity
    def _set_bg_opacity(self, v):   self._bg_opacity = v; self.update()
    bgOpacity = Property(float, _get_bg_opacity, _set_bg_opacity)

    def _get_title_y(self):         return self._title_y
    def _set_title_y(self, v):      self._title_y = v; self.update()
    titleY = Property(float, _get_title_y, _set_title_y)

    def _get_content_opacity(self):     return self._content_opacity
    def _set_content_opacity(self, v):  self._content_opacity = v; self.update()
    contentOpacity = Property(float, _get_content_opacity, _set_content_opacity)

    def _get_progress(self):        return self._progress
    def _set_progress(self, v):     self._progress = v; self.update()
    progress = Property(float, _get_progress, _set_progress)

    def _get_fade_out(self):        return self._fade_out
    def _set_fade_out(self, v):     self._fade_out = v; self.update()
    fadeOut = Property(float, _get_fade_out, _set_fade_out)

    # -------------------------------------------------------------------

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Sizing — 860 × 500 centred on screen
        screen = QApplication.primaryScreen().geometry()
        w, h = 860, 500
        self.setGeometry(
            (screen.width() - w) // 2,
            (screen.height() - h) // 2,
            w, h,
        )

        # Load assets
        self._bg_pixmap = QPixmap(str(BASE_DIR / "resources" / "splash_bg.jpg"))
        self._logo_pixmap = QPixmap()
        logo_path = BASE_DIR / "resources" / "app_icon.png"
        if not logo_path.exists():
            logo_path = BASE_DIR / "Logo.png"
        if logo_path.exists():
            self._logo_pixmap = QPixmap(str(logo_path)).scaled(
                72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        self._watermark_pixmap = QPixmap(str(BASE_DIR / "resources" / "kirigen_watermark.jpg")).scaled(
            160, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # Animatable state
        self._bg_opacity      = 0.0
        self._title_y         = -60.0    # starts above viewport
        self._content_opacity = 0.0
        self._progress        = 0.0
        self._fade_out        = 0.0

        # Status messages that cycle during loading
        self._status_messages = [
            "Initializing database…",
            "Loading NLP models…",
            "Preparing source library…",
            "Starting plagiarism engine…",
            "Almost ready…",
        ]
        self._status_index = 0
        self._status_text  = self._status_messages[0]

        self._build_animations()

    # -------------------------------------------------------------------
    # Animation setup
    # -------------------------------------------------------------------
    def _build_animations(self):
        ease_out = QEasingCurve.OutCubic
        ease_in  = QEasingCurve.InCubic

        # Phase 1: BG fade-in  (0–450 ms)
        anim_bg = QPropertyAnimation(self, b"bgOpacity")
        anim_bg.setDuration(450)
        anim_bg.setStartValue(0.0)
        anim_bg.setEndValue(1.0)
        anim_bg.setEasingCurve(ease_out)

        # Phase 2: title slides down (300–850 ms)
        anim_title = QPropertyAnimation(self, b"titleY")
        anim_title.setDuration(550)
        anim_title.setStartValue(-60.0)
        anim_title.setEndValue(0.0)
        anim_title.setEasingCurve(QEasingCurve.OutBack)

        # Phase 3: subtitle / logo fade-in (700–1100 ms)
        anim_content = QPropertyAnimation(self, b"contentOpacity")
        anim_content.setDuration(450)
        anim_content.setStartValue(0.0)
        anim_content.setEndValue(1.0)
        anim_content.setEasingCurve(ease_out)

        # Phase 4: progress bar fills (1000–3000 ms)
        anim_progress = QPropertyAnimation(self, b"progress")
        anim_progress.setDuration(2000)
        anim_progress.setStartValue(0.0)
        anim_progress.setEndValue(1.0)
        anim_progress.setEasingCurve(QEasingCurve.InOutSine)

        # Phase 5: fade out (3000–3400 ms)
        anim_fadeout = QPropertyAnimation(self, b"fadeOut")
        anim_fadeout.setDuration(400)
        anim_fadeout.setStartValue(0.0)
        anim_fadeout.setEndValue(1.0)
        anim_fadeout.setEasingCurve(ease_in)
        anim_fadeout.finished.connect(self._on_done)

        # Status message cycling timer  (every 420 ms during progress phase)
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(420)
        self._status_timer.timeout.connect(self._advance_status)

        # Schedule everything using single-shot timers for precise phasing
        QTimer.singleShot(0,    lambda: anim_bg.start())
        QTimer.singleShot(300,  lambda: anim_title.start())
        QTimer.singleShot(700,  lambda: anim_content.start())
        QTimer.singleShot(1000, lambda: (anim_progress.start(), self._status_timer.start()))
        QTimer.singleShot(3000, lambda: (self._status_timer.stop(), anim_fadeout.start()))

        # Keep references alive
        self._animations = [anim_bg, anim_title, anim_content, anim_progress, anim_fadeout]

    def _advance_status(self):
        self._status_index = (self._status_index + 1) % len(self._status_messages)
        self._status_text = self._status_messages[self._status_index]
        self.update()

    def _on_done(self):
        self.finished.emit()
        self.close()

    # -------------------------------------------------------------------
    # Custom painting
    # -------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        fade_alpha = self._fade_out  # 0→1: white overlay

        # ── Background image ──────────────────────────────────────────
        p.setOpacity(self._bg_opacity * (1.0 - fade_alpha))
        if not self._bg_pixmap.isNull():
            p.drawPixmap(0, 0, w, h, self._bg_pixmap)
        else:
            # Fallback gradient
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0, QColor("#112958"))
            grad.setColorAt(1, QColor("#273c66"))
            p.fillRect(0, 0, w, h, QBrush(grad))

        # Dark overlay so text reads cleanly on top of bg
        p.setOpacity(0.52 * (1.0 - fade_alpha))
        p.fillRect(0, 0, w, h, QColor(10, 18, 40))

        # ── Decorative teal accent line (left edge) ───────────────────
        p.setOpacity(self._bg_opacity * (1.0 - fade_alpha))
        pen = QPen(QColor("#21a7d0"), 4)
        p.setPen(pen)
        p.drawLine(0, 0, 0, h)

        # ── Logo ──────────────────────────────────────────────────────
        if not self._logo_pixmap.isNull():
            p.setOpacity(self._content_opacity * (1.0 - fade_alpha))
            logo_x = 54
            logo_y = int(h * 0.28 + self._title_y * 0.3)
            p.drawPixmap(logo_x, logo_y, self._logo_pixmap)

        # ── Trust line ───────────────────────────────────────────────
        title_base_y = int(h * 0.27 + self._title_y)
        p.setOpacity(self._bg_opacity * (1.0 - fade_alpha))
        p.setClipRect(0, 0, w, h)  # clip during slide

        trust_font = QFont("Segoe UI", 10, QFont.Normal)
        p.setFont(trust_font)
        p.setPen(QColor("#a0d4ea"))
        p.setOpacity(min(self._bg_opacity, 0.8) * (1.0 - fade_alpha))
        p.drawText(140, title_base_y, "R. C. Patel Educational Trust's")

        # ── Institution name ─────────────────────────────────────────
        inst_font = QFont("Segoe UI", 19, QFont.Bold)
        p.setFont(inst_font)
        p.setPen(QColor("#ffffff"))
        p.setOpacity(self._bg_opacity * (1.0 - fade_alpha))
        p.drawText(140, title_base_y + 28, "Institute of Management Research")
        p.drawText(140, title_base_y + 54, "and Development, Shirpur")

        # ── App name / tagline ───────────────────────────────────────
        p.setOpacity(self._content_opacity * (1.0 - fade_alpha))

        app_font = QFont("Segoe UI", 13, QFont.DemiBold)
        p.setFont(app_font)
        p.setPen(QColor("#21a7d0"))
        p.drawText(140, title_base_y + 82, "ResearchGuard  •  Plagiarism Verification System")

        accr_font = QFont("Segoe UI", 9)
        p.setFont(accr_font)
        p.setPen(QColor("#7fb8d0"))
        p.drawText(
            140, title_base_y + 100,
            "Approved by AICTE  •  Accredited B+ by NAAC  •  UGC 2018 Compliant"
        )

        # ── Progress bar ─────────────────────────────────────────────
        bar_y     = h - 72
        bar_left  = 54
        bar_right = w - 54
        bar_w     = bar_right - bar_left
        bar_h     = 5
        radius    = 3

        p.setOpacity(self._content_opacity * (1.0 - fade_alpha))

        # Track
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 30))
        p.drawRoundedRect(bar_left, bar_y, bar_w, bar_h, radius, radius)

        # Fill
        fill_w = int(bar_w * self._progress)
        if fill_w > 0:
            grad = QLinearGradient(bar_left, 0, bar_left + fill_w, 0)
            grad.setColorAt(0, QColor("#112958"))
            grad.setColorAt(0.5, QColor("#21a7d0"))
            grad.setColorAt(1, QColor("#7fe8ff"))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(bar_left, bar_y, fill_w, bar_h, radius, radius)

            # Glow dot at leading edge
            p.setBrush(QColor("#ffffff"))
            p.drawEllipse(bar_left + fill_w - 5, bar_y - 3, 10, bar_h + 6)

        # Status text
        status_font = QFont("Segoe UI", 9)
        p.setFont(status_font)
        p.setPen(QColor("#a0d4ea"))
        p.drawText(bar_left, bar_y - 10, self._status_text)

        # Version / right-side
        p.setPen(QColor("#4a7a9b"))
        p.drawText(
            QRect(0, bar_y - 12, w - bar_left, 16),
            Qt.AlignRight,
            "v2.0.0"
        )

        # ── KiriGen Tech watermark (bottom-right) ────────────────────
        p.setOpacity(self._content_opacity * 0.92 * (1.0 - fade_alpha))
        if not self._watermark_pixmap.isNull():
            wm_w = self._watermark_pixmap.width()
            wm_h = self._watermark_pixmap.height()
            wm_x = w - wm_w - 18
            wm_y = h - wm_h - 12
            # Rounded rect clipping mask for watermark
            path = QPainterPath()
            path.addRoundedRect(wm_x, wm_y, wm_w, wm_h, 6, 6)
            p.setClipPath(path)
            p.drawPixmap(wm_x, wm_y, self._watermark_pixmap)
            p.setClipping(False)

        # ── "Developed by" caption above watermark ────────────────────
        p.setOpacity(self._content_opacity * 0.6 * (1.0 - fade_alpha))
        dev_font = QFont("Segoe UI", 7.5)
        p.setFont(dev_font)
        p.setPen(QColor("#7fb8d0"))
        wm_x_ref = w - (self._watermark_pixmap.width() if not self._watermark_pixmap.isNull() else 160) - 18
        p.drawText(wm_x_ref, h - (self._watermark_pixmap.height() if not self._watermark_pixmap.isNull() else 54) - 16, "Developed by")

        # ── White fade-out overlay ────────────────────────────────────
        if fade_alpha > 0:
            p.setOpacity(fade_alpha)
            p.fillRect(0, 0, w, h, QColor("#f3f8f9"))

        p.end()
