from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QColor


class ProfileCard(QFrame):
    """Tarjeta de perfil interactiva — Light Premium 2026."""
    clicked = pyqtSignal()

    def __init__(self, accent_color_hex, parent=None):
        super().__init__(parent)
        self.accent_hex = accent_color_hex
        self.is_active = False
        self.r, self.g, self.b = self._hex_to_rgb(accent_color_hex)

        self.setFixedSize(220, 210)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Contenedor interno que flota
        self.inner = QFrame(self)
        self.inner.setGeometry(0, 15, 220, 185)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setColor(QColor(self.r, self.g, self.b, 30))
        self._shadow.setOffset(0, 6)
        self.inner.setGraphicsEffect(self._shadow)

        self.anim = QPropertyAnimation(self.inner, b"pos")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    def _hex_to_rgb(self, hex_str):
        h = hex_str.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def set_active(self, active: bool):
        self.is_active = active
        self.anim.stop()
        if active:
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 5))
            self.anim.start()
            self._shadow.setBlurRadius(28)
            self._shadow.setColor(QColor(self.r, self.g, self.b, 70))
            self._shadow.setOffset(0, 12)
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({self.r},{self.g},{self.b},0.08),
                        stop:1 rgba({self.r},{self.g},{self.b},0.03));
                    border: 2px solid rgba({self.r},{self.g},{self.b},0.75);
                    border-radius: 24px;
                }}
            """)
        else:
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 15))
            self.anim.start()
            self._shadow.setBlurRadius(20)
            self._shadow.setColor(QColor(self.r, self.g, self.b, 30))
            self._shadow.setOffset(0, 6)
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: #FFFFFF;
                    border: 1.5px solid rgba({self.r},{self.g},{self.b},0.18);
                    border-radius: 24px;
                }}
            """)

    def enterEvent(self, event):
        super().enterEvent(event)
        if not self.is_active:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 5))
            self.anim.start()
            self._shadow.setBlurRadius(28)
            self._shadow.setColor(QColor(self.r, self.g, self.b, 60))
            self._shadow.setOffset(0, 12)
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({self.r},{self.g},{self.b},0.06),
                        stop:1 rgba({self.r},{self.g},{self.b},0.02));
                    border: 2px solid rgba({self.r},{self.g},{self.b},0.50);
                    border-radius: 24px;
                }}
            """)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if not self.is_active:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 15))
            self.anim.start()
            self._shadow.setBlurRadius(20)
            self._shadow.setColor(QColor(self.r, self.g, self.b, 30))
            self._shadow.setOffset(0, 6)
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: #FFFFFF;
                    border: 1.5px solid rgba({self.r},{self.g},{self.b},0.18);
                    border-radius: 24px;
                }}
            """)

    def mousePressEvent(self, event):
        self.clicked.emit()


class PerfilPantalla(QDialog):
    """PASO 2: SELECCIÓN DE PERFIL — Light Premium 2026."""
    perfil_seleccionado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 480)
        self.selected_index = 1
        self._setup_ui()
        self.update_selection_ui()
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso2")
        except:
            pass

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        # Contenedor — blanco sin bordes duros
        self.container = QFrame()
        self.container.setObjectName("PerfilContainer")
        self.container.setStyleSheet("""
            QFrame#PerfilContainer {
                background: #FFFFFF;
                border-radius: 28px;
                border: none;
            }
        """)

        # Sombra exterior extra suave
        outer_shadow = QGraphicsDropShadowEffect(self)
        outer_shadow.setBlurRadius(45)
        outer_shadow.setColor(QColor(99, 102, 241, 35))
        outer_shadow.setOffset(0, 12)
        self.container.setGraphicsEffect(outer_shadow)
        root.addWidget(self.container)

        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Header (Integrado sin divisiones) ─────────────────────────────────
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        header_inner = QVBoxLayout(header_frame)
        header_inner.setContentsMargins(0, 24, 0, 8)

        badge = QLabel("⬡  IDENTIFICACIÓN DE ENTORNO  ⬡")
        badge.setStyleSheet("""
            color: #6366F1;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 4px;
            font-family: 'Segoe UI', sans-serif;
            background: transparent;
            border: none;
        """)
        badge.setAlignment(Qt.AlignCenter)
        header_inner.addWidget(badge)
        main_lay.addWidget(header_frame)

        # ── Content ───────────────────────────────────────────────────────────
        content = QVBoxLayout()
        content.setContentsMargins(36, 12, 36, 28)
        content.setSpacing(20)

        title = QLabel("Bienvenido")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 900;
            color: #0F172A;
            font-family: 'Segoe UI', 'Outfit', sans-serif;
            letter-spacing: -0.5px;
            background: transparent;
            border: none;
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Selecciona tu rol operativo para continuar")
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: #64748B;
            font-family: 'Segoe UI', sans-serif;
            background: transparent;
            border: none;
        """)
        subtitle.setAlignment(Qt.AlignCenter)

        content.addWidget(title)
        content.addWidget(subtitle)

        # Cards
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(20)

        self.btn_admin = self._create_card(
            icon="👔", title="ADMINISTRADOR",
            desc="Gestión · Inventarios · Reportes",
            accent="#10B981", tag="FULL ACCESS"
        )
        self.btn_admin.clicked.connect(lambda: self._elegir("admin"))

        self.btn_cajero = self._create_card(
            icon="🛒", title="CAJERO / POS",
            desc="Ventas rápidas · Cobro directo",
            accent="#3B82F6", tag="VENTA DIRECTA"
        )
        self.btn_cajero.clicked.connect(lambda: self._elegir("cajero"))

        cards_lay.addWidget(self.btn_admin)
        cards_lay.addWidget(self.btn_cajero)
        content.addLayout(cards_lay)

        # Hint teclado
        hint = QLabel("← → para navegar  ·  Enter para confirmar")
        hint.setStyleSheet("""
            font-size: 10px;
            color: #94A3B8;
            font-family: 'Segoe UI', sans-serif;
            background: transparent;
            border: none;
        """)
        hint.setAlignment(Qt.AlignCenter)
        content.addWidget(hint)
        


        main_lay.addLayout(content)



    def _create_card(self, icon, title, desc, accent, tag):
        r, g, b = tuple(int(accent.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

        btn = ProfileCard(accent)

        # Usamos btn.inner como el contenedor del layout del botón
        layout = QVBoxLayout(btn.inner)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Tag pill sin bordes duros
        tag_lbl = QLabel(tag)
        tag_lbl.setStyleSheet(f"""
            font-size: 8px; font-weight: 900; letter-spacing: 2px;
            color: rgba({r},{g},{b},1.0);
            background: rgba({r},{g},{b},0.10);
            border: none;
            border-radius: 6px; padding: 3px 8px;
            font-family: 'Segoe UI', sans-serif;
        """)
        tag_lbl.setAlignment(Qt.AlignCenter)
        tag_lbl.setFixedHeight(18)
        tag_wrap = QHBoxLayout()
        tag_wrap.addStretch()
        tag_wrap.addWidget(tag_lbl)
        tag_wrap.addStretch()

        # Icono más grande dentro de círculo
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(60, 60)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            font-size: 32px;
            background: rgba({r},{g},{b},0.08);
            border-radius: 30px;
            border: none;
        """)
        icon_wrap = QHBoxLayout()
        icon_wrap.addStretch()
        icon_wrap.addWidget(icon_lbl)
        icon_wrap.addStretch()

        tit_lbl = QLabel(title)
        tit_lbl.setStyleSheet(f"""
            font-size: 13px; font-weight: 900; color: #1E293B;
            letter-spacing: 1px; font-family: 'Segoe UI', sans-serif;
            border: none; background: transparent;
        """)
        tit_lbl.setAlignment(Qt.AlignCenter)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("""
            font-size: 10px; color: #64748B;
            font-family: 'Segoe UI', sans-serif;
            border: none; background: transparent;
        """)
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)

        layout.addLayout(tag_wrap)
        layout.addSpacing(2)
        layout.addLayout(icon_wrap)
        layout.addWidget(tit_lbl)
        layout.addWidget(desc_lbl)
        return btn

    def update_selection_ui(self):
        self.btn_admin.set_active(self.selected_index == 0)
        self.btn_cajero.set_active(self.selected_index == 1)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            self.selected_index = 1 if self.selected_index == 0 else 0
            self.update_selection_ui()
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._elegir("admin" if self.selected_index == 0 else "cajero")
            event.accept()
        else:
            super().keyPressEvent(event)

    def _elegir(self, rol):
        self.perfil_seleccionado.emit(rol)
        self.accept()

