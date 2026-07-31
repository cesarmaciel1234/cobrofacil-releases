"""
perfil_pantalla.py — Selector de Perfil
Paleta: Warm-Cold 2026 — fondo marfil cálido, acentos mezclados cálido+frío,
letras siempre bien marcadas y legibles.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QGraphicsDropShadowEffect, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QEvent
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QBrush, QKeyEvent

# PyQt6 Enum compatibility aliases
if hasattr(Qt, 'AlignmentFlag'):
    Qt.AlignCenter = Qt.AlignmentFlag.AlignCenter
    Qt.AlignLeft = Qt.AlignmentFlag.AlignLeft
    Qt.AlignRight = Qt.AlignmentFlag.AlignRight
if hasattr(Qt, 'CursorShape'):
    Qt.PointingHandCursor = Qt.CursorShape.PointingHandCursor
    Qt.ForbiddenCursor = Qt.CursorShape.ForbiddenCursor
if hasattr(Qt, 'WindowType'):
    Qt.FramelessWindowHint = Qt.WindowType.FramelessWindowHint
    Qt.Dialog = Qt.WindowType.Dialog
if hasattr(Qt, 'WidgetAttribute'):
    Qt.WA_TranslucentBackground = Qt.WidgetAttribute.WA_TranslucentBackground
if hasattr(Qt, 'MouseButton'):
    Qt.LeftButton = Qt.MouseButton.LeftButton
if hasattr(Qt, 'Key'):
    Qt.Key_Left = Qt.Key.Key_Left
    Qt.Key_Right = Qt.Key.Key_Right
    Qt.Key_Return = Qt.Key.Key_Return
    Qt.Key_Enter = Qt.Key.Key_Enter
if hasattr(Qt, 'KeyboardModifier'):
    Qt.NoModifier = Qt.KeyboardModifier.NoModifier


# ── Paleta global Warm-Cold ───────────────────────────────────────────────────
WC = {
    "bg":          "#FEF8EF",   # marfil cálido muy suave
    "surface":     "#FFFFFF",
    "text":        "#1C1917",   # marrón casi negro (cálido oscuro)
    "text2":       "#57534E",   # marrón medio (cálido)
    "text3":       "#A8A29E",   # stone claro
    "border":      "#E7E0D8",   # borde beige
    "shadow_warm": (217, 119,  6, 30),   # ámbar suave
    "shadow_cold": ( 99, 102, 241, 20),  # índigo suave
}

# Tarjetas — (accent_hex, bg_pill_hex, tag_text, tag_color)
CARD_STYLE = {
    "cajero": ("#0284C7", "#E0F2FE", "VENTA DIRECTA",  "#0369A1"),  # azul frío
    "admin":  ("#059669", "#DCFCE7", "FULL ACCESS",    "#047857"),  # verde templado
    "jefe":   ("#D97706", "#FEF3C7", "ACCESO GERENCIAL","#B45309"), # ámbar cálido
    "carteleria": ("#8B5CF6", "#EDE9FE", "MODO VISOR", "#6D28D9"), # púrpura vibrante
}


class ProfileCard(QFrame):
    """Tarjeta de perfil — Warm-Cold Premium 2026."""
    clicked = pyqtSignal()

    def __init__(self, role_key: str, icon: str, title: str, desc: str, parent=None):
        super().__init__(parent)
        accent, bg_pill, tag_text, tag_fg = CARD_STYLE[role_key]
        self._accent  = accent
        self._bg_pill = bg_pill
        self.is_active = False
        r, g, b = self._hex(accent)

        self.setFixedSize(230, 215)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Marco interno
        self.inner = QFrame(self)
        self.inner.setGeometry(0, 0, 230, 215)
        self._set_idle_style()

        # Layout interno
        lay = QVBoxLayout(self.inner)
        lay.setContentsMargins(18, 18, 18, 16)
        lay.setSpacing(0)

        # Tag pill
        tag = QLabel(tag_text)
        tag.setAlignment(Qt.AlignCenter)
        tag.setFixedHeight(20)
        tag.setStyleSheet(f"""
            font-size: 8px; font-weight: 900; letter-spacing: 2px;
            color: {tag_fg};
            background: {bg_pill};
            border: none; border-radius: 6px;
            padding: 2px 10px;
            font-family: 'Segoe UI', sans-serif;
        """)
        tag_wrap = QHBoxLayout()
        tag_wrap.addStretch(); tag_wrap.addWidget(tag); tag_wrap.addStretch()
        lay.addLayout(tag_wrap)
        lay.addSpacing(10)

        # Ícono
        ico = QLabel(icon)
        ico.setFixedSize(62, 62)
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet(f"""
            font-size: 30px;
            background: {bg_pill};
            border-radius: 18px; border: none;
        """)
        ico_wrap = QHBoxLayout()
        ico_wrap.addStretch(); ico_wrap.addWidget(ico); ico_wrap.addStretch()
        lay.addLayout(ico_wrap)
        lay.addSpacing(12)

        # Título
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet(f"""
            font-size: 13px; font-weight: 900; letter-spacing: 0.5px;
            color: {WC['text']};
            font-family: 'Segoe UI', 'Outfit', sans-serif;
            background: transparent; border: none;
        """)
        lay.addWidget(self.lbl_title)
        lay.addSpacing(4)

        # Descripción
        self.lbl_desc = QLabel(desc)
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet(f"""
            font-size: 10px; font-weight: 600; color: {WC['text2']};
            font-family: 'Segoe UI', sans-serif;
            background: transparent; border: none;
        """)
        lay.addWidget(self.lbl_desc)

    @staticmethod
    def _hex(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _set_idle_style(self):
        self.inner.setStyleSheet(f"""
            QFrame {{
                background: {WC['surface']};
                border-radius: 16px;
                border: 1px solid {WC['border']};
            }}
        """)

    def _set_hover_style(self):
        r, g, b = self._hex(self._accent)
        self.inner.setStyleSheet(f"""
            QFrame {{
                background: {WC['surface']};
                border-radius: 16px;
                border: 1px solid rgba({r},{g},{b},0.6);
            }}
        """)

    def _set_active_style(self):
        r, g, b = self._hex(self._accent)
        self.inner.setStyleSheet(f"""
            QFrame {{
                background: rgba({r},{g},{b},0.04);
                border-radius: 16px;
                border: 2px solid rgba({r},{g},{b},0.9);
            }}
        """)

    def set_active(self, active: bool):
        self.is_active = active
        if active:
            self._set_active_style()
        else:
            self._set_idle_style()

    def enterEvent(self, event):
        super().enterEvent(event)
        if not self.is_active:
            self._set_hover_style()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if not self.is_active:
            self._set_idle_style()

    def mousePressEvent(self, event):
        self.clicked.emit()


class PerfilPantalla(QDialog):
    """PASO 2: SELECCIÓN DE PERFIL — Warm-Cold Premium 2026."""
    perfil_seleccionado = pyqtSignal(str)

    # Orden visual: 0=cajero, 1=admin, 2=jefe
    _ROLES  = ["cajero", "admin", "jefe", "carteleria"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(1100, 490)
        self.selected_index = 0
        self._setup_ui()
        self.update_selection_ui()
        self._check_locked_profiles()
        try:
            from src.utils.qt_dpi import center_on_primary_screen
            center_on_primary_screen(self)
        except Exception:
            pass
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso2")
        except Exception:
            pass

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        # ── Contenedor principal ──────────────────────────────────────────────
        self.container = QFrame()
        self.container.setObjectName("PerfilContainer")
        self.container.setStyleSheet(f"""
            QFrame#PerfilContainer {{
                background: {WC['bg']};
                border-radius: 28px;
                border: none;
            }}
        """)
        outer_sh = QGraphicsDropShadowEffect(self)
        outer_sh.setBlurRadius(20)
        outer_sh.setColor(QColor(0, 0, 0, 30))
        outer_sh.setOffset(0, 4)
        self.container.setGraphicsEffect(outer_sh)
        root.addWidget(self.container)

        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Franja superior decorativa (gradiente cálido→frío) ────────────────
        stripe = QFrame()
        stripe.setFixedHeight(5)
        stripe.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0.00 #D97706,
                    stop:0.35 #EA580C,
                    stop:0.65 #6366F1,
                    stop:1.00 #0284C7);
                border-radius: 0px;
                border-top-left-radius: 28px;
                border-top-right-radius: 28px;
                border: none;
            }
        """)
        main_lay.addWidget(stripe)

        # ── Contenido ─────────────────────────────────────────────────────────
        content = QVBoxLayout()
        content.setContentsMargins(30, 16, 30, 32)
        content.setSpacing(0)

        # ── Header con Badge y Cruz para Cerrar ('✕') ────────────────────────
        header_lay = QHBoxLayout()
        header_lay.setContentsMargins(0, 0, 0, 0)

        # Spacer a la izquierda para contrapeso visual con el botón de cierre
        spacer_left = QFrame()
        spacer_left.setFixedSize(28, 28)
        spacer_left.setStyleSheet("background: transparent; border: none;")
        header_lay.addWidget(spacer_left)

        header_lay.addStretch()

        # Badge
        badge = QLabel("⬡  IDENTIFICACIÓN DE ENTORNO  ⬡")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet("""
            font-size: 9px; font-weight: 900; letter-spacing: 4px;
            color: #D97706;
            background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        header_lay.addWidget(badge)

        header_lay.addStretch()

        # Botón Cruz para cerrar
        btn_close = QPushButton("✕")
        btn_close.setObjectName("BtnClosePerfil")
        btn_close.setToolTip("Cerrar aplicación")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet(f"""
            QPushButton#BtnClosePerfil {{
                background: rgba(0, 0, 0, 0.04);
                color: {WC['text2']};
                border: none;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 900;
                font-family: 'Segoe UI', sans-serif;
            }}
            QPushButton#BtnClosePerfil:hover {{
                background: #FEE2E2;
                color: #DC2626;
            }}
            QPushButton#BtnClosePerfil:pressed {{
                background: #FCA5A5;
                color: #991B1B;
            }}
        """)
        btn_close.clicked.connect(self.reject)
        header_lay.addWidget(btn_close)

        content.addLayout(header_lay)
        content.addSpacing(10)

        # Título
        title = QLabel("Bienvenido")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 30px; font-weight: 900; letter-spacing: -1px;
            color: {WC['text']};
            font-family: 'Segoe UI', 'Outfit', sans-serif;
            background: transparent; border: none;
        """)
        content.addWidget(title)
        content.addSpacing(6)

        # Subtítulo
        subtitle = QLabel("Selecciona tu rol operativo para continuar")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: 12px; font-weight: 600; color: {WC['text2']};
            font-family: 'Segoe UI', sans-serif;
            background: transparent; border: none;
        """)
        content.addWidget(subtitle)
        content.addSpacing(28)

        # ── Cards ─────────────────────────────────────────────────────────────
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(20)

        self.btn_cajero = ProfileCard(
            "cajero", "🛒", "CAJERO / POS",
            "Ventas rápidas · Cobro directo")
        self.btn_cajero.clicked.connect(lambda: self._elegir("cajero"))

        self.btn_admin = ProfileCard(
            "admin", "👔", "ADMINISTRADOR",
            "Gestión · Inventarios · Reportes")
        self.btn_admin.clicked.connect(lambda: self._elegir("admin"))

        self.btn_jefe = ProfileCard(
            "jefe", "👑", "JEFE / DUEÑO",
            "Control total · Reportes · Cierres")
        self.btn_jefe.clicked.connect(lambda: self._elegir("jefe"))

        self.btn_carteleria = ProfileCard(
            "carteleria", "📺", "CARTELERÍA",
            "Pantalla Pública · Publicidad")
        self.btn_carteleria.clicked.connect(lambda: self._elegir("carteleria"))

        cards_lay.addStretch()
        cards_lay.addWidget(self.btn_cajero)
        cards_lay.addWidget(self.btn_admin)
        cards_lay.addWidget(self.btn_jefe)
        cards_lay.addWidget(self.btn_carteleria)
        cards_lay.addStretch()
        content.addLayout(cards_lay)
        content.addSpacing(22)

        # Hint teclado
        hint = QLabel("←  →  para navegar  ·  Enter para confirmar")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"""
            font-size: 10px; font-weight: 600; color: {WC['text3']};
            font-family: 'Segoe UI', sans-serif;
            background: transparent; border: none;
        """)
        content.addWidget(hint)

        main_lay.addLayout(content)

    def update_selection_ui(self):
        self.btn_cajero.set_active(self.selected_index == 0)
        self.btn_admin.set_active(self.selected_index == 1)
        self.btn_jefe.set_active(self.selected_index == 2)
        self.btn_carteleria.set_active(self.selected_index == 3)

    def _check_locked_profiles(self):
        try:
            self._apply_locked_profiles_ui()
        except Exception:
            self._roles_bloqueados = set()

    def _apply_locked_profiles_ui(self):
        from src.utils.candados import PerfilLocker
        
        # Diccionario para mapear roles a sus botones respectivos
        buttons_map = {
            "cajero": self.btn_cajero,
            "admin": self.btn_admin,
            "jefe": self.btn_jefe,
            "carteleria": self.btn_carteleria
        }
        
        # Bloquear visual y funcionalmente los botones de roles ya en uso
        self._roles_bloqueados = set()
        for i, rol in enumerate(self._ROLES):
            if PerfilLocker.check_is_locked(rol):
                self._roles_bloqueados.add(i)
                btn = buttons_map[rol]
                # Modificar el estilo para indicar bloqueo
                btn.inner.setStyleSheet(f"""
                    QFrame {{
                        background: #F8FAFC;
                        border-radius: 22px;
                        border: 1px dashed #CBD5E1;
                    }}
                """)
                btn.lbl_title.setText(btn.lbl_title.text() + " (EN USO)")
                btn.lbl_title.setStyleSheet(f"font-size: 13px; font-weight: 900; color: #DC2626; background: transparent; border: none;")
                btn.lbl_desc.setText("En ejecución. Clic para destrabar / cerrar instancia colgada.")
                btn.lbl_desc.setStyleSheet(f"font-size: 10px; font-weight: 600; color: #2563EB; background: transparent; border: none;")
                btn.setCursor(Qt.PointingHandCursor)
        
        # Si el seleccionado por defecto está bloqueado, avanzamos al siguiente libre
        if self.selected_index in self._roles_bloqueados and len(self._roles_bloqueados) < 4:
            self.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            delta = 1 if event.key() == Qt.Key_Right else -1
            # Buscar el siguiente rol
            original_idx = self.selected_index
            for _ in range(4):
                self.selected_index = (self.selected_index + delta) % 4
                break
            if original_idx != self.selected_index:
                self.update_selection_ui()
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._elegir(self._ROLES[self.selected_index])
            event.accept()
        else:
            super().keyPressEvent(event)

    def _elegir(self, rol):
        if self._ROLES.index(rol) in getattr(self, '_roles_bloqueados', set()):
            from PyQt6.QtWidgets import QMessageBox
            from src.utils.candados import PerfilLocker
            
            pid = PerfilLocker.get_locked_pid(rol)
            pid_txt = f" (PID {pid})" if pid else ""
            
            resp = QMessageBox.question(
                self,
                "⚠️ Instancia en Ejecución Detectada",
                f"El perfil '{rol.upper()}' ya figura abierto en este equipo{pid_txt}.\n\n"
                "Si el sistema se cerró con un error o quedó colgado en el Administrador de Tareas, "
                "¿deseas cerrar la instancia anterior y abrir este perfil ahora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if resp == QMessageBox.StandardButton.Yes:
                PerfilLocker.force_unlock_and_kill(rol)
                self._roles_bloqueados.discard(self._ROLES.index(rol))
                self.perfil_seleccionado.emit(rol)
                self.accept()
            return
            
        self.perfil_seleccionado.emit(rol)
        self.accept()

    # ── Arrastre de ventana con el mouse (Soporte multi-pantalla) ──────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and getattr(self, '_drag_pos', None) is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

