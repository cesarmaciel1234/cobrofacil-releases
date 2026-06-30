# src/jefe/componentes_visuales/jefe_card.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor

from src.jefe.theme_pro import THEME_PRO as L

class JefeCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, icon_char, accent, bg_soft, text_dark, parent=None):
        super().__init__(parent)
        self._locked   = False
        self._accent   = accent
        self._bg_soft  = bg_soft
        self._bg_hover = self._darken(bg_soft)
        r, g, b = self._hex2rgb(accent)

        self.setFixedSize(230, 200)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Marco interno flotante
        self.inner = QFrame(self)
        self.inner.setGeometry(0, 12, 230, 178)
        self.inner.setStyleSheet(f"""
            QFrame {{
                background: {L['surface']};
                border-radius: 24px;
                border: 1.5px solid {L['border']};
            }}
        """)


        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 22, 20, 18)
        layout.setSpacing(0)

        # Pill de ícono con color suave
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
        layout.addSpacing(14)

        # Título
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet(f"""
            font-size: 13px; font-weight: 800;
            color: {L['text']};
            font-family: 'Segoe UI', sans-serif;
            background: none; border: none;
        """)
        layout.addWidget(self.lbl_title)
        layout.addStretch()

        # Link acento
        self.lbl_link = QLabel(
            f"<span style='color:{accent}; font-size:9px; font-weight:900;"
            f" letter-spacing:1px;'>ABRIR  →</span>")
        self.lbl_link.setAlignment(Qt.AlignCenter)
        self.lbl_link.setStyleSheet("background: none; border: none;")
        layout.addWidget(self.lbl_link)

        # Animación lift
        self.anim = QPropertyAnimation(self.inner, b"pos")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    @staticmethod
    def _hex2rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def _darken(hex_color):
        """Oscurece levemente un color hex para el hover."""
        r, g, b = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        return f"#{max(0,r-15):02X}{max(0,g-15):02X}{max(0,b-15):02X}"

    def enterEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 2))
            self.anim.start()
            r, g, b = self._hex2rgb(self._accent)
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {L['surface']};
                    border-radius: 24px;
                    border: 2px solid rgba({r},{g},{b},0.55);
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 12))
            self.anim.start()
            r, g, b = self._hex2rgb(self._accent)
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {L['surface']};
                    border-radius: 24px;
                    border: 1.5px solid {L['border']};
                }}
            """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._locked:
            QMessageBox.warning(self, "Acceso Denegado",
                                "No tienes permisos para acceder a esta función.")
            return
        self.clicked.emit()
