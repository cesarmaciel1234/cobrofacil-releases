"""
perfil_pantalla.py — Selector de perfil (diseño plano, estable en monitores modestos).
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QKeyEvent

WC = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "text": "#0F172A",
    "text2": "#475569",
    "text3": "#94A3B8",
    "border": "#CBD5E1",
}

CARD_STYLE = {
    "cajero": ("#0284C7", "#E0F2FE", "VENTA DIRECTA", "#0369A1"),
    "admin": ("#059669", "#DCFCE7", "FULL ACCESS", "#047857"),
    "jefe": ("#D97706", "#FEF3C7", "ACCESO GERENCIAL", "#B45309"),
    "carteleria": ("#7C3AED", "#EDE9FE", "MODO VISOR", "#6D28D9"),
}


class ProfileCard(QFrame):
    """Tarjeta de perfil sin sombras ni animaciones."""
    clicked = pyqtSignal()

    def __init__(self, role_key: str, icon: str, title: str, desc: str,
                 card_w: int, card_h: int, parent=None):
        super().__init__(parent)
        accent, bg_pill, tag_text, tag_fg = CARD_STYLE[role_key]
        self._accent = accent
        self._bg_pill = bg_pill
        self.is_active = False
        self._card_w = card_w
        self._card_h = card_h

        self.setFixedSize(card_w, card_h)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.inner = QFrame()
        self.inner.setObjectName("ProfileCardInner")
        lay.addWidget(self.inner)

        inner_lay = QVBoxLayout(self.inner)
        inner_lay.setContentsMargins(14, 14, 14, 12)
        inner_lay.setSpacing(6)

        tag = QLabel(tag_text)
        tag.setAlignment(Qt.AlignCenter)
        tag.setStyleSheet(f"""
            font-size: 8px; font-weight: bold;
            color: {tag_fg}; background: {bg_pill};
            border: 1px solid {accent}; border-radius: 4px;
            padding: 2px 8px; font-family: 'Segoe UI', sans-serif;
        """)
        tag_wrap = QHBoxLayout()
        tag_wrap.addStretch()
        tag_wrap.addWidget(tag)
        tag_wrap.addStretch()
        inner_lay.addLayout(tag_wrap)

        ico = QLabel(icon)
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet(f"""
            font-size: 28px; background: {bg_pill};
            border: 1px solid {WC['border']}; border-radius: 12px;
            padding: 8px;
        """)
        inner_lay.addWidget(ico)

        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet(f"""
            font-size: 12px; font-weight: bold; color: {WC['text']};
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        inner_lay.addWidget(self.lbl_title)

        self.lbl_desc = QLabel(desc)
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet(f"""
            font-size: 10px; font-weight: 600; color: {WC['text2']};
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        inner_lay.addWidget(self.lbl_desc)

        self._set_idle_style()

    def _set_idle_style(self):
        self.inner.setStyleSheet(f"""
            QFrame#ProfileCardInner {{
                background: {WC['surface']};
                border-radius: 12px;
                border: 2px solid {WC['border']};
            }}
        """)

    def _set_active_style(self):
        self.inner.setStyleSheet(f"""
            QFrame#ProfileCardInner {{
                background: {WC['surface']};
                border-radius: 12px;
                border: 3px solid {self._accent};
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
            self.inner.setStyleSheet(f"""
                QFrame#ProfileCardInner {{
                    background: {WC['surface']};
                    border-radius: 12px;
                    border: 2px solid {self._accent};
                }}
            """)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if not self.is_active:
            self._set_idle_style()

    def mousePressEvent(self, event):
        self.clicked.emit()


class PerfilPantalla(QDialog):
    """PASO 2: selección de perfil."""
    perfil_seleccionado = pyqtSignal(str)
    _ROLES = ["cajero", "admin", "jefe", "carteleria"]

    def __init__(self, parent=None):
        super().__init__(parent)
        from src.utils.qt_dpi import profile_selector_size, center_on_primary_screen

        dlg_w, dlg_h, card_w, card_h = profile_selector_size()
        self._card_w = card_w
        self._card_h = card_h

        self.setWindowFlags(Qt.Dialog)
        self.setStyleSheet(f"QDialog {{ background-color: {WC['bg']}; }}")
        self.setFixedSize(dlg_w, dlg_h)
        self.selected_index = 0
        self._setup_ui()
        self.update_selection_ui()
        self._check_locked_profiles()
        try:
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
        root.setContentsMargins(16, 16, 16, 16)

        self.container = QFrame()
        self.container.setObjectName("PerfilContainer")
        self.container.setStyleSheet(f"""
            QFrame#PerfilContainer {{
                background: {WC['surface']};
                border-radius: 12px;
                border: 2px solid {WC['border']};
            }}
        """)
        root.addWidget(self.container)

        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(24, 20, 24, 24)
        main_lay.setSpacing(12)

        badge = QLabel("IDENTIFICACIÓN DE ENTORNO")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet("""
            font-size: 9px; font-weight: bold; color: #D97706;
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        main_lay.addWidget(badge)

        title = QLabel("Bienvenido")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 26px; font-weight: bold; color: {WC['text']};
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        main_lay.addWidget(title)

        subtitle = QLabel("Seleccioná tu rol operativo para continuar")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: 12px; font-weight: 600; color: {WC['text2']};
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        main_lay.addWidget(subtitle)

        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(12)

        self.btn_cajero = ProfileCard(
            "cajero", "🛒", "CAJERO / POS", "Ventas rápidas · Cobro directo",
            self._card_w, self._card_h)
        self.btn_cajero.clicked.connect(lambda: self._elegir("cajero"))

        self.btn_admin = ProfileCard(
            "admin", "👔", "ADMINISTRADOR", "Gestión · Inventarios · Reportes",
            self._card_w, self._card_h)
        self.btn_admin.clicked.connect(lambda: self._elegir("admin"))

        self.btn_jefe = ProfileCard(
            "jefe", "👑", "JEFE / DUEÑO", "Control total · Reportes · Cierres",
            self._card_w, self._card_h)
        self.btn_jefe.clicked.connect(lambda: self._elegir("jefe"))

        self.btn_carteleria = ProfileCard(
            "carteleria", "📺", "CARTELERÍA", "Pantalla pública · Publicidad",
            self._card_w, self._card_h)
        self.btn_carteleria.clicked.connect(lambda: self._elegir("carteleria"))

        cards_lay.addStretch()
        for btn in (self.btn_cajero, self.btn_admin, self.btn_jefe, self.btn_carteleria):
            cards_lay.addWidget(btn)
        cards_lay.addStretch()
        main_lay.addLayout(cards_lay)

        hint = QLabel("← → para navegar · Enter para confirmar")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"""
            font-size: 10px; font-weight: 600; color: {WC['text3']};
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        main_lay.addWidget(hint)

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

        buttons_map = {
            "cajero": self.btn_cajero,
            "admin": self.btn_admin,
            "jefe": self.btn_jefe,
            "carteleria": self.btn_carteleria,
        }

        self._roles_bloqueados = set()
        for i, rol in enumerate(self._ROLES):
            if PerfilLocker.check_is_locked(rol):
                self._roles_bloqueados.add(i)
                btn = buttons_map[rol]
                btn.inner.setStyleSheet("""
                    QFrame#ProfileCardInner {
                        background: #F1F5F9;
                        border-radius: 12px;
                        border: 2px dashed #94A3B8;
                    }
                """)
                btn.lbl_title.setText(btn.lbl_title.text() + " (EN USO)")
                btn.lbl_title.setStyleSheet(
                    "font-size: 12px; font-weight: bold; color: #94A3B8; background: transparent; border: none;"
                )
                btn.lbl_desc.setText("Esta instancia ya está en ejecución en esta terminal.")
                btn.lbl_desc.setStyleSheet(
                    "font-size: 10px; font-weight: 600; color: #94A3B8; background: transparent; border: none;"
                )
                btn.setCursor(Qt.ForbiddenCursor)

        if self.selected_index in self._roles_bloqueados and len(self._roles_bloqueados) < 4:
            self.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            delta = 1 if event.key() == Qt.Key_Right else -1
            original_idx = self.selected_index
            for _ in range(4):
                self.selected_index = (self.selected_index + delta) % 4
                if self.selected_index not in getattr(self, '_roles_bloqueados', set()):
                    break
            if original_idx != self.selected_index:
                self.update_selection_ui()
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.selected_index not in getattr(self, '_roles_bloqueados', set()):
                self._elegir(self._ROLES[self.selected_index])
            event.accept()
        else:
            super().keyPressEvent(event)

    def _elegir(self, rol):
        if self._ROLES.index(rol) in getattr(self, '_roles_bloqueados', set()):
            import winsound
            winsound.Beep(800, 200)
            return
        self.perfil_seleccionado.emit(rol)
        self.accept()
