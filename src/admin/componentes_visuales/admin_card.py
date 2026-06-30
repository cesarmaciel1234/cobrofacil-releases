from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor

# ── Paleta de colores suaves por módulo ───────────────────────────────────────
# (accent_hex, bg_suave_hex)
SOFT = {
    "indigo":  ("#6366F1", "#EEF2FF"),
    "blue":    ("#3B82F6", "#EFF6FF"),
    "emerald": ("#10B981", "#ECFDF5"),
    "amber":   ("#F59E0B", "#FFFBEB"),
    "rose":    ("#F43F5E", "#FFF1F2"),
    "violet":  ("#8B5CF6", "#F5F3FF"),
    "sky":     ("#0EA5E9", "#F0F9FF"),
    "pink":    ("#EC4899", "#FDF2F8"),
    "slate":   ("#64748B", "#F8FAFC"),
    "teal":    ("#14B8A6", "#F0FDFA"),
}

# ─────────────────────────────────────────────────────────────────────────────
#  AdminCard — Light Soft 2026: blanco + borde color, lift animado
# ─────────────────────────────────────────────────────────────────────────────
class AdminCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, icon_char, palette_key, subtitle=""):
        super().__init__()
        self._locked      = False
        self._palette_key = palette_key
        accent, bg_soft   = SOFT.get(palette_key, SOFT["slate"])
        r, g, b = self._hex2rgb(accent)
        self._accent = accent
        self._r, self._g, self._b = r, g, b

        self.setFixedSize(220, 200)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Marco flotante
        self.inner = QFrame(self)
        self.inner.setGeometry(0, 12, 220, 178)
        self.inner.setObjectName("DashboardCard")
        self.inner.setStyleSheet("""
            QFrame#DashboardCard {
                border-radius: 20px;
            }
        """)

        # Sombra de color suave
        self._sh = QGraphicsDropShadowEffect(self)
        self._sh.setBlurRadius(18)
        self._sh.setColor(QColor(r, g, b, 30))
        self._sh.setOffset(0, 5)
        self.inner.setGraphicsEffect(self._sh)

        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(0)

        # Ícono con pill de color suave
        icon_pill = QLabel(icon_char)
        icon_pill.setFixedSize(56, 56)
        icon_pill.setAlignment(Qt.AlignCenter)
        icon_pill.setStyleSheet(f"""
            font-size: 28px;
            background: {bg_soft};
            border-radius: 16px;
            border: none;
        """)
        h_icon = QHBoxLayout()
        h_icon.addStretch()
        h_icon.addWidget(icon_pill)
        h_icon.addStretch()
        layout.addLayout(h_icon)
        layout.addSpacing(12)

        # Título
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet("""
            font-size: 12px; font-weight: 800;
            font-family: 'Segoe UI', sans-serif;
            background: none; border: none;
        """)
        layout.addWidget(self.lbl_title)

        if subtitle:
            self.sub = QLabel(subtitle)
            self.sub.setAlignment(Qt.AlignCenter)
            self.sub.setStyleSheet("""
                font-size: 9px;
                background: none; border: none;
                font-family: 'Segoe UI', sans-serif;
            """)
            layout.addWidget(self.sub)

        layout.addStretch()

        # Link acento
        self.lbl_link = QLabel(
            f"<span style='color:{accent}; font-size:9px;"
            f" font-weight:900; letter-spacing:1px;'>ABRIR  →</span>")
        self.lbl_link.setAlignment(Qt.AlignCenter)
        self.lbl_link.setStyleSheet("background: none; border: none;")
        layout.addWidget(self.lbl_link)

        # Animación lift
        self.anim = QPropertyAnimation(self.inner, b"pos")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    @staticmethod
    def _hex2rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def enterEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 2))
            self.anim.start()
            r, g, b = self._r, self._g, self._b
            self.inner.setStyleSheet(f"""
                QFrame#DashboardCard {{
                    border-radius: 20px;
                    border: 2px solid rgba({r},{g},{b},0.50);
                }}
            """)
            self._sh.setBlurRadius(26)
            self._sh.setColor(QColor(r, g, b, 65))
            self._sh.setOffset(0, 10)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 12))
            self.anim.start()
            r, g, b = self._r, self._g, self._b
            self.inner.setStyleSheet("""
                QFrame#DashboardCard {
                    border-radius: 20px;
                }
            """)
            self._sh.setBlurRadius(18)
            self._sh.setColor(QColor(r, g, b, 30))
            self._sh.setOffset(0, 5)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._locked:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Acceso Denegado",
                                "No tienes permisos para acceder a esta función.")
            return
        self.clicked.emit()

    def set_locked(self, locked: bool):
        self._locked = locked
        if locked:
            self.setCursor(Qt.ForbiddenCursor)
            self.lbl_link.setText(
                "<span style='color:#CBD5E1; font-size:9px; font-weight:900;'>BLOQUEADO</span>")
            self.inner.setStyleSheet("""
                QFrame#DashboardCard {
                    border-radius: 20px;
                }
            """)
        else:
            self.setCursor(Qt.PointingHandCursor)
            self.lbl_link.setText(
                f"<span style='color:{self._accent}; font-size:9px;"
                f" font-weight:900; letter-spacing:1px;'>ABRIR  →</span>")
            self.inner.setStyleSheet("""
                QFrame#DashboardCard {
                    border-radius: 20px;
                }
            """)
