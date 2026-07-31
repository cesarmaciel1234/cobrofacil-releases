"""
perfil_pantalla.py — Lanzador Maestro Autónomo de Perfiles
Paleta: Warm-Cold 2026 — fondo marfil cálido, acentos mezclados cálido+frío,
letras siempre bien marcadas y legibles.

Lanzador Hub Central: Permite iniciar múltiples perfiles de forma autónoma
en subprocesos independientes sin colisionar ni cerrarse entre sí.
"""
import os
import sys
import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QGraphicsDropShadowEffect, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QEvent, QTimer
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
        self._tag_fg = tag_fg
        self._original_title = title
        self._original_desc = desc
        self.is_active = False
        r, g, b = self._hex(accent)

        self.setFixedSize(230, 215)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Marco interno
        self.inner = QFrame(self)
        self.inner.setGeometry(0, 0, 230, 215)

        # Layout interno
        lay = QVBoxLayout(self.inner)
        lay.setContentsMargins(18, 18, 18, 16)
        lay.setSpacing(0)

        # Tag pill
        self.tag = QLabel(tag_text)
        self.tag.setAlignment(Qt.AlignCenter)
        self.tag.setFixedHeight(20)
        self.tag.setStyleSheet(f"""
            font-size: 8px; font-weight: 900; letter-spacing: 2px;
            color: {tag_fg};
            background: {bg_pill};
            border: none; border-radius: 6px;
            padding: 2px 10px;
            font-family: 'Segoe UI', sans-serif;
        """)
        tag_wrap = QHBoxLayout()
        tag_wrap.addStretch(); tag_wrap.addWidget(self.tag); tag_wrap.addStretch()
        lay.addLayout(tag_wrap)
        lay.addSpacing(10)

        # Ícono
        ico = QLabel(icon)
        ico.setAlignment(Qt.AlignCenter)
        ico.setFixedHeight(50)
        ico.setStyleSheet(f"""
            font-size: 34px; background: {bg_pill};
            border: none; border-radius: 14px;
        """)
        lay.addWidget(ico)
        lay.addSpacing(12)

        # Título
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet(f"""
            font-size: 13px; font-weight: 900; letter-spacing: 0.5px;
            color: {WC['text']}; background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        lay.addWidget(self.lbl_title)
        lay.addSpacing(4)

        # Descripción
        self.lbl_desc = QLabel(desc)
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setStyleSheet(f"""
            font-size: 10px; font-weight: 500;
            color: {WC['text2']}; background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        lay.addWidget(self.lbl_desc)

        self._set_idle_style()

    def _hex(self, hex_str):
        h = hex_str.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _set_idle_style(self):
        self.inner.setStyleSheet(f"""
            QFrame {{
                background: {WC['surface']};
                border-radius: 22px;
                border: 2px solid {WC['border']};
            }}
        """)
        self.lbl_title.setText(self._original_title)
        self.lbl_title.setStyleSheet(f"font-size: 13px; font-weight: 900; color: {WC['text']}; background: transparent; border: none;")
        self.lbl_desc.setText(self._original_desc)
        self.lbl_desc.setStyleSheet(f"font-size: 10px; font-weight: 500; color: {WC['text2']}; background: transparent; border: none;")

    def set_active(self, active: bool):
        self.is_active = active
        r, g, b = self._hex(self._accent)
        if active:
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {WC['surface']};
                    border-radius: 22px;
                    border: 3px solid {self._accent};
                }}
            """)
        else:
            self._set_idle_style()

    def set_launching_state(self):
        self.inner.setStyleSheet("""
            QFrame {
                background: #EFF6FF;
                border-radius: 22px;
                border: 3px solid #2563EB;
            }
        """)
        self.tag.setText("⏳ INICIANDO MÓDULO...")
        self.tag.setStyleSheet("""
            font-size: 8px; font-weight: 900; letter-spacing: 1px;
            color: #1D4ED8; background: #DBEAFE;
            border: none; border-radius: 6px; padding: 2px 8px;
        """)
        self.lbl_title.setText("🚀 ARRANCANDO...")
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 900; color: #1E40AF; background: transparent; border: none;")
        self.lbl_desc.setText("Inicializando subproceso...\nPor favor aguarde unos segundos")
        self.lbl_desc.setStyleSheet("font-size: 10px; font-weight: 700; color: #2563EB; background: transparent; border: none;")
        self.setCursor(Qt.CursorShape.WaitCursor)

    def set_retry_state(self, count: int, max_count: int = 3):
        self.inner.setStyleSheet("""
            QFrame {
                background: #FFFBEB;
                border-radius: 22px;
                border: 2.5px solid #F59E0B;
            }
        """)
        self.tag.setText(f"🔄 RE-INTENTO AUTO ({count}/{max_count})")
        self.tag.setStyleSheet("""
            font-size: 8px; font-weight: 900; letter-spacing: 1px;
            color: #B45309; background: #FEF3C7;
            border: none; border-radius: 6px; padding: 2px 8px;
        """)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 900; color: #B45309; background: transparent; border: none;")
        self.lbl_desc.setText(f"Se detectó caída. Re-levantando subproceso ({count}/{max_count})...")
        self.lbl_desc.setStyleSheet("font-size: 10px; font-weight: 700; color: #D97706; background: transparent; border: none;")
        self.setCursor(Qt.CursorShape.WaitCursor)

    def set_failed_state(self):
        self.inner.setStyleSheet("""
            QFrame {
                background: #FEF2F2;
                border-radius: 22px;
                border: 2.5px solid #EF4444;
            }
        """)
        self.tag.setText("⚠️ DETENIDO (3 CAÍDAS)")
        self.tag.setStyleSheet("""
            font-size: 8px; font-weight: 900; letter-spacing: 1px;
            color: #B91C1C; background: #FEE2E2;
            border: none; border-radius: 6px; padding: 2px 8px;
        """)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 900; color: #B91C1C; background: transparent; border: none;")
        self.lbl_desc.setText("Falló 3 veces seguidas. Pausado por seguridad.\nClic para reintentar manual")
        self.lbl_desc.setStyleSheet("font-size: 10px; font-weight: 700; color: #DC2626; background: transparent; border: none;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class PerfilPantalla(QDialog):
    perfil_seleccionado = pyqtSignal(str)

    _ROLES = ["cajero", "admin", "jefe", "carteleria"]

    def __init__(self, is_master_launcher=True, parent=None):
        super().__init__(parent)
        self.is_master_launcher = is_master_launcher
        self._subprocesos = {} # { "cajero": subprocess.Popen, ... }
        self._reintentos = { "cajero": 0, "admin": 0, "jefe": 0, "carteleria": 0 }
        self._max_reintentos = 3
        self.selected_index = 0
        self._roles_bloqueados = set()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1080, 480)
        from src.utils.candados import MASTER_WINDOW_TITLE
        self.setWindowTitle(MASTER_WINDOW_TITLE)

        self._setup_ui()
        self.update_selection_ui()

        # En modo Lanzador Maestro, monitorear activamente el estado de los subprocesos
        if self.is_master_launcher:
            self._timer_monitor = QTimer(self)
            self._timer_monitor.setInterval(1500)
            self._timer_monitor.timeout.connect(self._check_locked_profiles)
            self._timer_monitor.start()

        self._check_locked_profiles()

    def _setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(12, 12, 12, 12)

        # Contenedor principal con borde redondeado y sombra doble
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {WC['bg']};
                border-radius: 28px;
                border: 1.5px solid {WC['border']};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(217, 119, 6, 25))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        main_lay.addWidget(card)

        content = QVBoxLayout(card)
        content.setContentsMargins(36, 20, 36, 24)
        content.setSpacing(0)

        # ── Barra Superior (Subtítulo y Botón Cerrar) ──────────────────────────
        top_bar = QHBoxLayout()
        sub = QLabel("✦  LANZADOR MAESTRO AUTÓNOMO DE ENTORNO  ✦")
        sub.setAlignment(Qt.AlignLeft)
        sub.setStyleSheet(f"""
            font-size: 9px; font-weight: 800; letter-spacing: 3px;
            color: #D97706; background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        top_bar.addWidget(sub)
        top_bar.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setToolTip("Cerrar Lanzador Maestro")
        btn_close.setStyleSheet("""
            QPushButton {
                background: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5;
                border-radius: 14px; font-weight: 900; font-size: 13px;
            }
            QPushButton:hover { background: #DC2626; color: #FFFFFF; }
        """)
        btn_close.clicked.connect(self.reject)
        top_bar.addWidget(btn_close)

        content.addLayout(top_bar)
        content.addSpacing(6)

        # Título principal
        title = QLabel("Bienvenido a CobroFacil PRO 2026")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 26px; font-weight: 900; letter-spacing: -0.5px;
            color: {WC['text']}; background: transparent; border: none;
            font-family: 'Segoe UI Black', 'Segoe UI', sans-serif;
        """)
        content.addWidget(title)
        content.addSpacing(4)

        subtitle = QLabel("Selecciona y ejecuta tus roles operativos de forma 100% independiente")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: 12px; font-weight: 500;
            color: {WC['text2']}; background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        content.addWidget(subtitle)
        content.addSpacing(22)

        # ── Fila de 4 tarjetas ────────────────────────────────────────────────
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(16)

        self.btn_cajero = ProfileCard("cajero", "🛒", "CAJERO / POS", "Ventas rápidas · Cobro directo")
        self.btn_admin  = ProfileCard("admin",  "👔", "ADMINISTRADOR", "Gestión · Inventarios · Reportes")
        self.btn_jefe   = ProfileCard("jefe",   "👑", "JEFE / DUEÑO",  "Control total · Reportes · Cierres")
        self.btn_carteleria = ProfileCard("carteleria", "📺", "CARTELERÍA", "Pantalla Pública · Publicidad")

        self.btn_cajero.clicked.connect(lambda: self._select_and_choose(0))
        self.btn_admin.clicked.connect(lambda: self._select_and_choose(1))
        self.btn_jefe.clicked.connect(lambda: self._select_and_choose(2))
        self.btn_carteleria.clicked.connect(lambda: self._select_and_choose(3))

        cards_lay.addWidget(self.btn_cajero)
        cards_lay.addWidget(self.btn_admin)
        cards_lay.addWidget(self.btn_jefe)
        cards_lay.addWidget(self.btn_carteleria)

        content.addLayout(cards_lay)
        content.addSpacing(18)

        # Ayuda de teclado
        hint = QLabel("← → para navegar · Enter / Clic para lanzar perfil autónomo")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"""
            font-size: 10px; font-weight: 600; color: {WC['text3']};
            font-family: 'Segoe UI', sans-serif;
            background: transparent; border: none;
        """)
        content.addWidget(hint)

        main_lay.addWidget(card)

    def _select_and_choose(self, idx: int):
        self.selected_index = idx
        self.update_selection_ui()
        self._elegir(self._ROLES[idx])

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
            "carteleria": self.btn_carteleria
        }
        
        self._roles_bloqueados = set()
        for i, rol in enumerate(self._ROLES):
            btn = buttons_map[rol]
            pid = PerfilLocker.get_locked_pid(rol)
            is_locked = PerfilLocker.check_is_locked(rol)
            proc = self._subprocesos.get(rol)

            if is_locked and pid:
                self._roles_bloqueados.add(i)
                self._reintentos[rol] = 0
                btn.inner.setStyleSheet("""
                    QFrame {
                        background: #F0FDF4;
                        border-radius: 22px;
                        border: 2.5px solid #16A34A;
                    }
                """)
                btn.tag.setText("🟢 AUTÓNOMO EN EJECUCIÓN")
                btn.tag.setStyleSheet("""
                    font-size: 8px; font-weight: 900; letter-spacing: 1px;
                    color: #15803D; background: #DCFCE7;
                    border: none; border-radius: 6px; padding: 2px 8px;
                """)
                btn.lbl_title.setStyleSheet("font-size: 13px; font-weight: 900; color: #15803D; background: transparent; border: none;")
                btn.lbl_desc.setText(f"🟢 ACTIVO (PID {pid})\nClic para administrar / reiniciar")
                btn.lbl_desc.setStyleSheet("font-size: 10px; font-weight: 700; color: #16A34A; background: transparent; border: none;")
            else:
                # Si el proceso fue iniciado previamente y se cerró/cayó
                if proc is not None and proc.poll() is not None:
                    retry_count = self._reintentos.get(rol, 0)
                    if retry_count < self._max_reintentos:
                        self._reintentos[rol] = retry_count + 1
                        btn.set_retry_state(self._reintentos[rol], self._max_reintentos)
                        # Re-lanzar de forma autónoma tras 1 segundo
                        QTimer.singleShot(1000, lambda r=rol: self._lanzar_proceso_autonomo(r))
                    else:
                        btn.set_failed_state()
                else:
                    if self._reintentos.get(rol, 0) >= self._max_reintentos:
                        btn.set_failed_state()
                    else:
                        btn._set_idle_style()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            delta = 1 if event.key() == Qt.Key_Right else -1
            original_idx = self.selected_index
            self.selected_index = (self.selected_index + delta) % 4
            if original_idx != self.selected_index:
                self.update_selection_ui()
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._elegir(self._ROLES[self.selected_index])
            event.accept()
        else:
            super().keyPressEvent(event)

    def _elegir(self, rol):
        from src.utils.candados import PerfilLocker
        pid = PerfilLocker.get_locked_pid(rol)
        is_locked = PerfilLocker.check_is_locked(rol)

        # Al hacer clic manual, resetear el contador de reintentos
        self._reintentos[rol] = 0

        if is_locked and pid:
            resp = QMessageBox.question(
                self,
                "⚙️ Gestión de Instancia Autónoma",
                f"El perfil '{rol.upper()}' ya se encuentra en ejecución (PID {pid}).\n\n"
                "¿Qué acción deseas realizar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            # Yes = Reiniciar/Cerrar la instancia colgada y re-lanzar
            # No = Cerrar la instancia colgada únicamente
            # Cancel = No hacer nada
            if resp == QMessageBox.StandardButton.Yes:
                PerfilLocker.force_unlock_and_kill(rol)
                self._roles_bloqueados.discard(self._ROLES.index(rol))
                self._lanzar_proceso_autonomo(rol)
            elif resp == QMessageBox.StandardButton.No:
                PerfilLocker.force_unlock_and_kill(rol)
                self._roles_bloqueados.discard(self._ROLES.index(rol))
                self._apply_locked_profiles_ui()
            return

        # Si no está en ejecución, lanzar proceso autónomo
        self._lanzar_proceso_autonomo(rol)

    def _lanzar_proceso_autonomo(self, rol):
        from PyQt6.QtWidgets import QApplication

        buttons_map = {
            "cajero": self.btn_cajero,
            "admin": self.btn_admin,
            "jefe": self.btn_jefe,
            "carteleria": self.btn_carteleria
        }

        btn = buttons_map.get(rol)
        if btn:
            btn.set_launching_state()
            app = QApplication.instance()
            if app:
                app.processEvents()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        main_script = os.path.join(base_dir, "main.py")

        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--role", rol]
        else:
            cmd = [sys.executable, main_script, "--role", rol]

        try:
            proc = subprocess.Popen(cmd)
            self._subprocesos[rol] = proc
            QTimer.singleShot(1500, self._apply_locked_profiles_ui)
        except Exception as e:
            if btn:
                btn._set_idle_style()
            QMessageBox.critical(self, "Error al Lanzar", f"No se pudo iniciar el proceso autónomo para {rol}:\n{e}")

    # ── Arrastre de ventana con el mouse (Soporte multi-pantalla) ──────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and getattr(self, '_drag_pos', None) is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
