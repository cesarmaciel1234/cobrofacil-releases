# src/jefe/componentes_visuales/jefe_card.py
import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QPixmap


class JefeCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, icon_input, accent, bg_soft, text_dark, parent=None):
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
        self.inner.setObjectName("DashboardCard")
        self.inner.setStyleSheet("""
            QFrame#DashboardCard {
                border-radius: 24px;
            }
        """)


        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 22, 20, 18)
        layout.setSpacing(0)

        # Pill de ícono con color suave - soporta PNG o emoji
        icon_pill = QLabel()
        icon_pill.setFixedSize(56, 56)
        icon_pill.setAlignment(Qt.AlignCenter)

        # Intentar cargar PNG si es una ruta
        if isinstance(icon_input, str) and (icon_input.endswith('.png') or icon_input.endswith('.jpg') or icon_input.endswith('.svg')):
            icon_path = self._resolve_icon_path(icon_input)
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon_pill.setPixmap(scaled)
                    icon_pill.setStyleSheet(f"""
                        background: {bg_soft};
                        border-radius: 16px;
                        border: none;
                    """)
                else:
                    # Fallback a emoji si PNG falla
                    icon_pill.setText("📊")
                    icon_pill.setStyleSheet(f"""
                        font-size: 28px;
                        background: {bg_soft};
                        border-radius: 16px;
                        border: none;
                    """)
            else:
                # Fallback a emoji si no existe el archivo
                icon_pill.setText("📊")
                icon_pill.setStyleSheet(f"""
                    font-size: 28px;
                    background: {bg_soft};
                    border-radius: 16px;
                    border: none;
                """)
        else:
            # Usar emoji como antes
            icon_pill.setText(icon_input if icon_input else "📊")
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
            font-size: 13px; font-weight: 400; color: {text_dark};
            letter-spacing: 0px;
            font-family: 'Segoe UI', sans-serif;
            background: transparent; border: none;
        """)
        layout.addWidget(self.lbl_title)
        layout.addStretch()

        self.lbl_link = QLabel("Abrir →")
        self.lbl_link.setAlignment(Qt.AlignCenter)
        self.lbl_link.setStyleSheet(
            f"color: {accent}; font-size: 11px; font-weight: 400;"
            " letter-spacing: 0px; background: transparent; border: none;"
        )
        layout.addWidget(self.lbl_link)

        # Animación eliminada para PCs de bajos recursos

    def _resolve_icon_path(self, icon_path):
        """Resuelve la ruta del icono buscando en múltiples ubicaciones."""
        from src.utils.paths import get_base_path

        # Si es ruta absoluta
        if os.path.isabs(icon_path):
            return icon_path

        # Buscar en src/jefe/assets/
        base = get_base_path()
        candidates = [
            os.path.join(base, "src", "jefe", "assets", icon_path),
            os.path.join(base, "src", "jefe", "assets", icon_path.replace('.png', '.svg')),
            os.path.join(base, "src", "assets", icon_path),
            os.path.join(base, "src", "assets", icon_path.replace('.png', '.svg')),
        ]

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

        return None

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
            r, g, b = self._hex2rgb(self._accent)
            self.inner.setStyleSheet(f"""
                QFrame#DashboardCard {{
                    border-radius: 24px;
                    border: 2px solid rgba({r},{g},{b},0.55);
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._locked:
            r, g, b = self._hex2rgb(self._accent)
            self.inner.setStyleSheet(f"""
                QFrame#DashboardCard {{
                    border-radius: 24px;
                }}
            """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._locked:
            QMessageBox.warning(self, "Acceso Denegado",
                                "No tienes permisos para acceder a esta función.")
            return
        self.clicked.emit()
