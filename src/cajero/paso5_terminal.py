from src.utils.qt_compat import qt_exec
import os, sys, threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import src.utils.qt_compat  # noqa: F401 — enums Qt6 (Qt + widgets)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
    QAbstractItemView, QListWidget, QListWidgetItem, QDialog, QPushButton, QGridLayout,
    QComboBox, QDoubleSpinBox, QGraphicsDropShadowEffect, QMessageBox, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QDate, QTime, QObject, pyqtSignal, QRect, QEvent
from PyQt6.QtGui import QColor, QFont, QPen, QPainter
from datetime import datetime
import time
import logging
logger = logging.getLogger(__name__)

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager
from src.cajero.paso7_cierre import Paso7CierreCaja
from src.cajero.paso8_historial import DialogoHistorialDia, fmt_moneda
from src.config import config
from src.hardware.printer import printer_manager
from src.hardware.cash_drawer import drawer_manager
try:
    import winsound
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False

try:
    from src.ui_components.virtual_keyboard_paso5 import VirtualKeyboardPaso5 as VirtualKeyboard
    HAS_KEYBOARD = True
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Modulo de teclado virtual no disponible: {e}")
    HAS_KEYBOARD = False


def fmt_moneda_sin_centavos(val):
    try:
        return f"${float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "$0,00"

def parse_float_safe(val_str):
    try:
        val_str = str(val_str).replace("$", "").strip()
        # Si tiene formato europeo/argentino con coma decimal: 1.234,56
        if "," in val_str:
            # Quitamos los puntos de miles y cambiamos la coma por punto
            val_str = val_str.replace(".", "").replace(",", ".")
        # Si no tiene coma, asumimos que el punto ya es el decimal (formato inglés: 1234.56)
        return float(val_str)
    except Exception:
        return 0.0
class DialogoAtencion(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(500, 300)
        self.setStyleSheet("background-color: #008080; border: 3px solid #888;")
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Mensaje de Atención")
        header.setStyleSheet("color: red; font-size: 28px; font-weight: bold; border: none;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Body
        body = QLabel("Cancelar\n¿Desea eliminar el artículo?")
        body.setStyleSheet("color: white; font-size: 22px; font-weight: bold; border: none;")
        body.setAlignment(Qt.AlignCenter)
        layout.addWidget(body)
        
        layout.addStretch()
        
        # Footer
        footer = QHBoxLayout()
        lbl_ent = QLabel("ENT-Continuar")
        lbl_ent.setStyleSheet("color: white; font-size: 20px; font-weight: bold; border: none;")
        lbl_esc = QLabel("ESC-NO")
        lbl_esc.setStyleSheet("color: white; font-size: 20px; font-weight: bold; border: none; background-color: #666; padding: 5px;")
        footer.addWidget(lbl_ent)
        footer.addStretch()
        footer.addWidget(lbl_esc)
        layout.addLayout(footer)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

SCAN_ROW_BG = "#EFF6FF"
NAV_ROW_BORDER = "#F59E0B"


class NavRowBorderOverlay(QWidget):
    """Marco naranja flotante: no se ancla a celdas, sigue la fila activa con flechas."""
    def __init__(self, tabla):
        super().__init__(tabla.viewport())
        self.tabla = tabla
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

    def _sync_geometry(self):
        vp = self.tabla.viewport()
        if vp:
            self.setGeometry(vp.rect())

    def sync_and_repaint(self):
        self._sync_geometry()
        t = self.tabla
        if t.hasFocus() and t.currentRow() >= 0:
            self.show()
            self.raise_()
            self.update()
        else:
            self.hide()

    def paintEvent(self, event):
        t = self.tabla
        if not t.hasFocus() or t.currentRow() < 0:
            return
        model = t.model()
        if model is None or t.columnCount() <= 0:
            return
        row = t.currentRow()
        r0 = t.visualRect(model.index(row, 0))
        rN = t.visualRect(model.index(row, t.columnCount() - 1))
        if r0.width() <= 0 or rN.width() <= 0:
            return
        rect = QRect(r0.topLeft(), rN.bottomRight()).adjusted(2, 2, -2, -2)
        if not self.rect().intersects(rect):
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(NAV_ROW_BORDER), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect, 6, 6)
        p.end()


class DialogoEditarCantidad(QDialog):
    def __init__(self, cant_actual, nombre, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(540, 340)
        self.setStyleSheet("QDialog { background: transparent; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        box = QFrame()
        box.setObjectName("EditCantDialog")
        box.setStyleSheet("""
            QFrame#EditCantDialog {
                background: #FFFFFF;
                border: 4px solid #437EE8;
                border-radius: 12px;
            }
            QFrame#EditCantDialog QLabel {
                background: transparent;
                border: none;
                color: #1E293B;
                font-family: 'Segoe UI';
                font-weight: 800;
            }
            QFrame#EditCantDialog QDoubleSpinBox {
                font-size: 48px;
                padding: 10px;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                background: #F8FAFC;
                color: #1E293B;
            }
            QFrame#EditCantDialog QPushButton {
                border-radius: 8px;
                padding: 14px 12px;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 0.5px;
                min-height: 48px;
            }
        """)
        outer.addWidget(box)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        lbl_prod = QLabel(f"MODIFICAR: {nombre.upper()}")
        lbl_prod.setObjectName("EditCantProducto")
        lbl_prod.setAlignment(Qt.AlignCenter)
        lbl_prod.setStyleSheet("font-size: 15px; color: #64748B; background: transparent; border: none;")
        layout.addWidget(lbl_prod)

        lbl_title = QLabel("CANTIDAD")
        lbl_title.setObjectName("EditCantTitle")
        lbl_title.setStyleSheet("font-size: 26px; font-weight: 900; color: #1E3A8A; background: transparent; border: none;")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(0.001, 9999.999)
        self.spin.setDecimals(3)
        self.spin.setValue(cant_actual)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.setFocus()
        self.spin.selectAll()
        self.spin.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        layout.addWidget(self.spin)

        btns = QHBoxLayout()
        btns.setSpacing(12)
        btn_ok = QPushButton("✅ CONFIRMAR (ENTER)")
        btn_ok.setStyleSheet("background: #10B981; color: white; border: none;")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton("❌ CANCELAR (ESC)")
        btn_cancel.setStyleSheet("background: #EF4444; color: white; border: none;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_ok, 1)
        btns.addWidget(btn_cancel, 1)
        layout.addLayout(btns)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def get_value(self):
        return self.spin.value()


# ──────────────────────────────────────────────────────────────
# ESTADO GLOBAL DEL CAJERO ACTIVO (módulo compartido)
# ──────────────────────────────────────────────────────────────
from src.cajero.cajero_activo import CajeroActivo


class DialogoPIN(QDialog):
    """Diálogo súper simple de PIN de 4 dígitos."""
    PIN_VALIDO = "1234"

    def __init__(self, cajero_nombre, parent=None):
        super().__init__(parent)
        self.cajero_nombre = cajero_nombre
        self.ok = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(340, 280)
        self.setStyleSheet("background: white; border-radius: 16px; border: 2px solid #1E3A8A;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 25, 30, 25)
        lay.setSpacing(12)

        lbl = QLabel(f"👤  {self.cajero_nombre.upper()}")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E3A8A; border: none;")
        lay.addWidget(lbl)

        lbl2 = QLabel("Ingresa el PIN:")
        lbl2.setAlignment(Qt.AlignCenter)
        lbl2.setStyleSheet("font-size: 13px; color: #64748b; border: none;")
        lay.addWidget(lbl2)

        self.txt_pin = QLineEdit()
        self.txt_pin.setEchoMode(QLineEdit.Password)
        self.txt_pin.setMaxLength(6)
        self.txt_pin.setAlignment(Qt.AlignCenter)
        self.txt_pin.setStyleSheet("""
            QLineEdit {
                font-size: 32px; font-weight: 900; letter-spacing: 8px;
                border: 2px solid #cbd5e1; border-radius: 10px;
                padding: 10px; background: #f8fafc; color: #1e293b;
            }
            QLineEdit:focus { border-color: #3B82F6; }
        """)
        self.txt_pin.returnPressed.connect(self._verificar)
        lay.addWidget(self.txt_pin)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #EF4444; font-weight: bold; border: none;")
        lay.addWidget(self.lbl_err)

        btn = QPushButton("✅  INGRESAR")
        btn.setStyleSheet("""
            QPushButton {
                background: #1E3A8A; color: white; font-size: 14px; font-weight: 900;
                border-radius: 10px; padding: 12px;
            }
            QPushButton:hover { background: #2563EB; }
        """)
        btn.clicked.connect(self._verificar)
        lay.addWidget(btn)

        QTimer.singleShot(100, self.txt_pin.setFocus)

    def _verificar(self):
        from src.utils.pin_auth import verify_pin
        entered_pin = self.txt_pin.text().strip()
        
        # Buscar el PIN en la base de datos para el usuario con este nombre
        res = db_manager.execute_query("SELECT pin FROM usuarios WHERE LOWER(username) = ?", (self.cajero_nombre.lower(),))
        pin_valido = None
        
        if res and res[0]['pin']:
            pin_valido = str(res[0]['pin'])
        else:
            # Fallback secundario: si no coincide el nombre configurado del cajero físico, usar el del usuario logueado en la sesión
            curr_usr = config.current_user if hasattr(config, 'current_user') else None
            if curr_usr:
                res_curr = db_manager.execute_query("SELECT pin FROM usuarios WHERE id = ?", (curr_usr.get("id"),))
                if res_curr and res_curr[0]['pin']:
                    pin_valido = str(res_curr[0]['pin'])

        if verify_pin(entered_pin, pin_valido or ""):
            self.ok = True
            self.accept()
        else:
            self.lbl_err.setText("❌ PIN incorrecto")
            self.txt_pin.clear()
            self.txt_pin.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            return  # No se puede saltar el PIN con ESC
        super().keyPressEvent(event)


class DialogoRetiroEfectivo(QDialog):
    """Diálogo industrial rápido para retirar efectivo de caja (F5)."""
    def __init__(self, efectivo_actual, parent=None):
        super().__init__(parent)
        self.efectivo_actual = efectivo_actual
        self.monto_retirado = 0.0
        self.motivo = ""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(400, 390)
        self.setStyleSheet("background: white; border-radius: 16px; border: 3px solid #EA580C;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 18, 30, 18)
        lay.setSpacing(10)

        lbl = QLabel("💸  RETIRO DE EFECTIVO")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #EA580C; border: none;")
        lay.addWidget(lbl)

        lbl_disp = QLabel(f"Disponible en Caja: ${self.efectivo_actual:,.2f}")
        lbl_disp.setAlignment(Qt.AlignCenter)
        lbl_disp.setStyleSheet("font-size: 13px; color: #64748b; font-weight: bold; border: none;")
        lay.addWidget(lbl_disp)

        lbl2 = QLabel("Monto a retirar ($):")
        lbl2.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border: none;")
        lay.addWidget(lbl2)

        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignCenter)
        sugerido = max(0.0, self.efectivo_actual - 40000) if self.efectivo_actual > 50000 else 0.0
        if sugerido > 0:
            self.txt_monto.setText(f"{int(sugerido)}")
        self.txt_monto.setStyleSheet("""
            QLineEdit {
                font-size: 32px; font-weight: 900; color: #DC2626;
                border: 2px solid #cbd5e1; border-radius: 10px;
                padding: 6px; background: #f8fafc;
            }
            QLineEdit:focus { border-color: #EA580C; }
        """)
        lay.addWidget(self.txt_monto)

        lbl_m = QLabel("Motivo / Descripción (Opcional):")
        lbl_m.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border: none;")
        lay.addWidget(lbl_m)

        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText("Ej: Pago proveedor, Viáticos...")
        self.txt_motivo.setStyleSheet("""
            QLineEdit {
                font-size: 14px; color: #1E293B; font-weight: 600;
                border: 2px solid #cbd5e1; border-radius: 8px;
                padding: 8px; background: #f8fafc;
            }
            QLineEdit:focus { border-color: #EA580C; background: white; }
        """)
        self.txt_motivo.returnPressed.connect(self._procesar)
        self.txt_monto.returnPressed.connect(self.txt_motivo.setFocus)
        lay.addWidget(self.txt_motivo)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none;")
        lay.addWidget(self.lbl_err)

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background: #F1F5F9; color: #475569; font-weight: bold; padding: 10px; border-radius: 8px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("🚀 RETIRAR")
        btn_ok.setStyleSheet("background: #EA580C; color: white; font-weight: 900; font-size: 14px; padding: 10px; border-radius: 8px;")
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel); h_btns.addWidget(btn_ok)
        lay.addLayout(h_btns)

        QTimer.singleShot(100, self.txt_monto.setFocus)
        QTimer.singleShot(120, self.txt_monto.selectAll)

    def _procesar(self):
        try:
            val = float(self.txt_monto.text().strip())
            if val <= 0:
                self.lbl_err.setText("⚠️ Ingresa un monto mayor a 0")
                return
            if val > self.efectivo_actual:
                self.lbl_err.setText("⚠️ No hay suficiente efectivo en caja")
                return
            self.monto_retirado = val
            mot = self.txt_motivo.text().strip()
            self.motivo = mot if mot else "Retiro rápido de efectivo en terminal"
            self.accept()
        except ValueError:
            self.lbl_err.setText("⚠️ Monto inválido")


class DialogoIngresoEfectivo(QDialog):
    """Diálogo premium 3D para ingresar dinero a la caja (F6)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monto_ingresado = 0.0
        self.motivo = ""
        self.tipo_ingreso = "CAMBIO"
        self.cliente_id = None
        self.cliente_nombre = ""
        self.deuda_actual = 0.0
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(500, 600)
        self.setStyleSheet("background: white; border-radius: 16px; border: 3px solid #10B981;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 22, 30, 22)
        lay.setSpacing(15)

        lbl = QLabel("💵  INGRESO DE DINERO")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #10B981; border: none;")
        lay.addWidget(lbl)

        lbl_sub = QLabel("Seleccione el concepto del ingreso físico")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748b; font-weight: bold; border: none;")
        lay.addWidget(lbl_sub)
        
        # Grid de opciones 3D
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.btn_cambio = self._crear_btn_opcion("🪙", "CAMBIO", "Fondo Fijo", "#3B82F6")
        self.btn_fiado = self._crear_btn_opcion("👥", "FIADO", "Pago de Deuda", "#10B981")
        self.btn_otros = self._crear_btn_opcion("📦", "OTROS", "Varios", "#6366F1")
        
        self.btn_cambio.clicked.connect(lambda: self._set_modo("CAMBIO"))
        self.btn_fiado.clicked.connect(lambda: self._set_modo("FIADO"))
        self.btn_otros.clicked.connect(lambda: self._set_modo("OTROS"))
        
        grid.addWidget(self.btn_cambio, 0, 0)
        grid.addWidget(self.btn_fiado, 0, 1)
        grid.addWidget(self.btn_otros, 0, 2)
        lay.addLayout(grid)
        
        # Stack para paneles dinámicos
        from PyQt6.QtWidgets import QStackedWidget, QComboBox
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;")
        
        # Panel Normal (Cambio/Otros)
        panel_normal = QWidget()
        pn_lay = QVBoxLayout(panel_normal)
        pn_lay.setContentsMargins(20, 20, 20, 20)
        self.lbl_titulo_monto = QLabel("Monto a ingresar ($):")
        self.lbl_titulo_monto.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border: none;")
        pn_lay.addWidget(self.lbl_titulo_monto)
        
        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignCenter)
        self.txt_monto.setStyleSheet("""
            QLineEdit {
                font-size: 36px; font-weight: 900; color: #059669;
                border: 2px solid #cbd5e1; border-radius: 10px;
                padding: 8px; background: white;
            }
            QLineEdit:focus { border-color: #10B981; }
        """)
        self.txt_monto.returnPressed.connect(self._procesar)
        pn_lay.addWidget(self.txt_monto)
        
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Descripción (Opcional)...")
        self.txt_desc.setStyleSheet("font-size: 14px; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; background: white;")
        pn_lay.addWidget(self.txt_desc)
        self.stack.addWidget(panel_normal)
        
        # Panel Fiado (compartido con Fiado Express — modo abono)
        from src.cajero.widgets.panel_cliente_fiado import PanelClienteFiado

        panel_fiado = QWidget()
        pf_lay = QVBoxLayout(panel_fiado)
        pf_lay.setContentsMargins(20, 10, 20, 10)
        self.panel_fiado = PanelClienteFiado(modo="abono", theme="light")
        if self.panel_fiado.txt_monto is not None:
            self.panel_fiado.txt_monto.returnPressed.connect(self._procesar)
        pf_lay.addWidget(self.panel_fiado)
        self.stack.addWidget(panel_fiado)
        
        lay.addWidget(self.stack)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none;")
        lay.addWidget(self.lbl_err)

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background: #F1F5F9; color: #475569; font-weight: bold; padding: 12px; border-radius: 8px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("🚀 CONFIRMAR")
        btn_ok.setStyleSheet("background: #10B981; color: white; font-weight: 900; font-size: 15px; padding: 12px; border-radius: 8px;")
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel)
        h_btns.addWidget(btn_ok)
        lay.addLayout(h_btns)

        self._set_modo("CAMBIO")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self.txt_monto.setFocus)

    def _crear_btn_opcion(self, icono, titulo, subtitulo, color):
        btn = QPushButton()
        btn.setFixedHeight(80)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: white; border: 2px solid #e2e8f0; border-radius: 12px; text-align: center;
            }}
            QPushButton:hover {{ border-color: {color}; background: #f8fafc; }}
            QPushButton:checked {{ border-color: {color}; background: {color}; color: white; }}
        """)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        
        lay = QVBoxLayout(btn)
        lay.setAlignment(Qt.AlignCenter)
        lbl_i = QLabel(icono)
        lbl_i.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        lbl_i.setAlignment(Qt.AlignCenter)
        
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("font-weight: 900; font-size: 12px; border: none; background: transparent;")
        lbl_t.setAlignment(Qt.AlignCenter)
        
        lay.addWidget(lbl_i)
        lay.addWidget(lbl_t)
        return btn

    def _set_modo(self, modo):
        self.tipo_ingreso = modo
        self.btn_cambio.setChecked(modo == "CAMBIO")
        self.btn_fiado.setChecked(modo == "FIADO")
        self.btn_otros.setChecked(modo == "OTROS")
        
        if modo == "FIADO":
            self.stack.setCurrentIndex(1)
            self.panel_fiado.cargar_clientes_abono()
            self.panel_fiado.focus_monto()
        else:
            self.stack.setCurrentIndex(0)
            self.txt_monto.setFocus()
            self.txt_monto.selectAll()
            if modo == "CAMBIO":
                self.txt_desc.setText("Fondo fijo / Cambio")
                self.txt_desc.hide()
            else:
                self.txt_desc.setText("")
                self.txt_desc.show()

    def _procesar(self):
        try:
            if self.tipo_ingreso == "FIADO":
                ok, err = self.panel_fiado.validar()
                if not ok:
                    self.lbl_err.setText(err)
                    return
                data = self.panel_fiado.cliente_actual()
                self.monto_ingresado = self.panel_fiado.monto()
                self.deuda_actual = self.panel_fiado.deuda_actual()
                self.cliente_id = data["id"]
                self.cliente_nombre = data["nombre"]
                self.motivo = f"Abono Fiado: {self.cliente_nombre}"
            else:
                val = float(self.txt_monto.text().strip())
                if val <= 0:
                    self.lbl_err.setText("⚠️ Ingresa un monto mayor a 0")
                    return
                self.monto_ingresado = val
                desc = self.txt_desc.text().strip()
                if self.tipo_ingreso == "CAMBIO":
                    self.motivo = "Ingreso de Cambio / Fondo Fijo"
                else:
                    self.motivo = desc if desc else "Otros Ingresos Manuales"
                    
            self.accept()
        except ValueError:
            self.lbl_err.setText("⚠️ Monto inválido")



class DialogoCandado(QDialog):
    """
    Pantalla de bloqueo clásica. Muestra dos botones/paneles grandes simétricos:
    [1] CAJERO (azul) y [2] AUXILIAR (verde).
    Ambos requieren validación de PIN para acceder y reconfiguran su hardware respectivo.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        if parent:
            self.setFixedSize(parent.size())
        else:
            self.setFixedSize(1280, 800)
        self._build()

    def _build(self):
        from src.config import config
        # Fondo desenfocado leve (el blur real lo hace el padre)
        fondo = QFrame(self)
        fondo.setGeometry(0, 0, self.width(), self.height())
        fondo.setStyleSheet("background: rgba(248, 250, 252, 0.65);")

        # Contenedor central más alto (500px como pidió el usuario) y con bordes suaves
        w, h = 600, 500
        container = QFrame(self)
        container.setFixedSize(w, h)
        container.move((self.width() - w) // 2, (self.height() - h) // 2)
        container.setStyleSheet("background: white; border-radius: 20px; border: 1px solid #CBD5E1;")
        
        # Efecto de elevación para el cuadro central
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)

        main_lay = QVBoxLayout(container)
        main_lay.setContentsMargins(40, 40, 40, 40)
        main_lay.setSpacing(25)

        # Título superior
        lbl_icon = QLabel("🔒  TERMINAL BLOQUEADA")
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 26px; font-weight: 900; color: #1E293B; letter-spacing: 2px; border: none;")
        main_lay.addWidget(lbl_icon)

        lbl_sub = QLabel("Selecciona tu perfil de caja para continuar:")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 14px; font-weight: 600; color: #64748B; border: none;")
        main_lay.addWidget(lbl_sub)

        # Layout horizontal para las dos tarjetas simétricas
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(20)

        name_c1 = config.get("nombre_cajero_1", "CAJERO")
        name_c2 = config.get("nombre_cajero_2", "AUXILIAR")

        # --- TARJETA [1] CAJERO (AZUL) ---
        self.btn_cajero = QPushButton()
        self.btn_cajero.setFixedSize(240, 160)
        self.btn_cajero.setCursor(Qt.PointingHandCursor)
        self.btn_cajero.setStyleSheet("""
            QPushButton {
                background: white; border-radius: 16px;
                border: 3px solid #1E3A8A;
            }
            QPushButton:hover { background: #EFF6FF; border-color: #3B82F6; }
            QPushButton:pressed { background: #DBEAFE; }
        """)
        lay_c1 = QVBoxLayout(self.btn_cajero)
        lay_c1.setContentsMargins(15, 20, 15, 20)
        
        lbl_t1 = QLabel(f"🔵  [1]  {name_c1.upper()}")
        lbl_t1.setAlignment(Qt.AlignCenter)
        lbl_t1.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E3A8A; background: transparent; border: none;")
        lbl_p1 = QLabel("Perfil Principal\n(Cajón e impresora 1)")
        lbl_p1.setAlignment(Qt.AlignCenter)
        lbl_p1.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; background: transparent; border: none;")
        lay_c1.addWidget(lbl_t1); lay_c1.addWidget(lbl_p1)
        self.btn_cajero.clicked.connect(lambda: self._pedir_pin(1))

        # --- TARJETA [2] AUXILIAR (VERDE) ---
        self.btn_auxiliar = QPushButton()
        self.btn_auxiliar.setFixedSize(240, 160)
        self.btn_auxiliar.setCursor(Qt.PointingHandCursor)
        self.btn_auxiliar.setStyleSheet("""
            QPushButton {
                background: white; border-radius: 16px;
                border: 3px solid #059669;
            }
            QPushButton:hover { background: #ECFDF5; border-color: #10B981; }
            QPushButton:pressed { background: #D1FAE5; }
        """)
        lay_c2 = QVBoxLayout(self.btn_auxiliar)
        lay_c2.setContentsMargins(15, 20, 15, 20)
        
        lbl_t2 = QLabel(f"🟢  [2]  {name_c2.upper()}")
        lbl_t2.setAlignment(Qt.AlignCenter)
        lbl_t2.setStyleSheet("font-size: 18px; font-weight: 900; color: #059669; background: transparent; border: none;")
        lbl_p2 = QLabel("Perfil Secundario\n(Cajón e impresora 2)")
        lbl_p2.setAlignment(Qt.AlignCenter)
        lbl_p2.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; background: transparent; border: none;")
        lay_c2.addWidget(lbl_t2); lay_c2.addWidget(lbl_p2)
        self.btn_auxiliar.clicked.connect(lambda: self._pedir_pin(2))

        cards_lay.addWidget(self.btn_cajero)
        cards_lay.addWidget(self.btn_auxiliar)
        main_lay.addLayout(cards_lay)
        
        main_lay.addStretch()

        # Mensaje IA / Aprendizaje
        ai_tip = QLabel("🤖 Misma sesión de turno: el auxiliar cobra con su PIN y activa su cajón físico. Usa F8 para bloquear al salir.")
        ai_tip.setAlignment(Qt.AlignCenter)
        ai_tip.setWordWrap(True)
        ai_tip.setStyleSheet("font-size: 13px; color: #0284C7; font-weight: bold; background: #E0F2FE; padding: 12px; border-radius: 8px; border: none;")
        main_lay.addWidget(ai_tip)

    def _pedir_pin(self, numero_cajero):
        from src.config import config
        nombre = config.get(f"nombre_cajero_{numero_cajero}", f"Cajero {numero_cajero}").upper()
        dlg = DialogoPIN(nombre, parent=self)
        if qt_exec(dlg) and dlg.ok:
            CajeroActivo.set(numero_cajero)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            return  # No se puede escapar sin acción
        if event.key() == Qt.Key_1:
            self._pedir_pin(1)
            return
        if event.key() == Qt.Key_2:
            self._pedir_pin(2)
            return










class Paso5Terminal(QWidget):
    request_admin_jump = pyqtSignal()
    request_chatbot_toggle = pyqtSignal()
    """
    PASO 5: TERMINAL INDUSTRIAL EXACTA (100% Foto + Búsqueda Rápida)
    """
    def __init__(self):
        super().__init__()
        self.txt_scan = None
        self.setup_ui()
        self.apply_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000)
        
        # Timer para evitar que el buscador se trabe al leer códigos rápido
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_busqueda)
        
        # Timer de alta velocidad (150ms) para auto-foco instantáneo en el escáner (haga click donde haga, vuelve al instante)
        self.autofocus_timer = QTimer(self)
        self.autofocus_timer.timeout.connect(self.asegurar_foco_escaner)
        self.autofocus_timer.start(150)
        
        # Timer de stock crítico (cada 5 minutos)
        if config.get("stock_alerta_activa", True):
            self.stock_timer = QTimer(self)
            self.stock_timer.timeout.connect(self.verificar_stock_minimo)
            self.stock_timer.start(300000) # 300,000 ms = 5 mins
            QTimer.singleShot(2000, self.verificar_stock_minimo)
            
        # Timer de autocierre (cada 60 segundos)
        if config.get("cierre_auto_activo", False):
            self.autoclose_timer = QTimer(self)
            self.autoclose_timer.timeout.connect(self.verificar_autocierre)
            self.autoclose_timer.start(60000) # 60,000 ms = 1 min
        # Monitor de Seguridad: Delegado al Motor Global en MainWindow
        pass

        # El chatbot animado ahora se inicializa en segundo plano desde main.py
        # para que esté listo de forma instantánea al presionar el botón
        self.chatbot_process = None

        self.tickets_espera = []
        self.cliente_id = None
        self.cliente_nombre = "Consumidor Final"
        self.descuento_general = 0.0
        self.timer_alerta_espera = QTimer(self)
        self.timer_alerta_espera.timeout.connect(self._alerta_tickets_espera)
        self.timer_alerta_espera.start(120000)

    def _stock_disponible(self, p, p_id):
        if p_id == "000":
            return None
        try:
            if hasattr(p, "keys") and "stock" in p.keys():
                return float(p["stock"] or 0)
            if isinstance(p, dict) and "stock" in p:
                return float(p["stock"] or 0)
        except (TypeError, ValueError):
            pass
        res = db_manager.execute_query("SELECT stock FROM productos WHERE id=?", (p_id,))
        return float(res[0]["stock"] or 0) if res else 0.0

    def _validar_stock(self, p, p_id, cantidad_necesaria):
        if p_id == "000" or config.get("opt_stock_negativo", False):
            return True
        stock = self._stock_disponible(p, p_id)
        if stock is None:
            return True
        if cantidad_necesaria > stock + 1e-9:
            QMessageBox.warning(
                self,
                "Sin stock",
                f"Stock insuficiente.\n\nDisponible: {stock:g}\nSolicitado: {cantidad_necesaria:g}",
            )
            return False
        return True



    def _refresh_urgencia_stock_banner(self):
        activo = bool(config.get("opt_stock_negativo", False))
        if hasattr(self, "urgencia_stock_banner"):
            self.urgencia_stock_banner.set_active(activo)

    def refresh_terminal_title(self):
        title = config.get('business_name', 'Punto de Venta [20.09.02]')
        self.lbl_terminal_title.setText(title)
        self._orig_title = title

    def refresh_status_bar(self):
        import socket, uuid
        from src.utils.paths import get_base_path
        base_path = get_base_path().lower()
        db_path = db_manager.db_path.lower()
        
        # Determinar si la base de datos es local (Maestra) o remota (Cliente)
        is_local = base_path in db_path or not db_path or db_path == "punpro.db"
        estado_text = "Estado:           MAESTRA" if is_local else "Estado:           CLIENTE"
        self.lbl_estado.setText(estado_text)
        
        # Generar código de instalación único a partir de la dirección MAC
        mac_str = f"{uuid.getnode():012X}"
        formatted_mac = f"№ {mac_str[:4]}-{mac_str[4:8]}-{mac_str[8:]}"
        self.lbl_instalacion.setText(formatted_mac)
        
        # Iniciar latido de red y conteo dinámico si no existe el timer
        if not hasattr(self, 'red_timer'):
            self.red_timer = QTimer(self)
            self.red_timer.timeout.connect(self.actualizar_red_heartbeat)
            self.red_timer.start(15000) # Latido cada 15 segundos
            # Ejecutar una vez al inicio
            QTimer.singleShot(500, self.actualizar_red_heartbeat)

    def actualizar_red_heartbeat(self):
        try:
            import socket
            caja_id = config.get("caja_id", 1)
            hostname = socket.gethostname().upper()
            
            # Registrar presencia de este terminal
            db_manager.registrar_heartbeat(caja_id, hostname)
            
            # Obtener cantidad de terminales activos
            total_activos = db_manager.get_terminales_activos_count()
            
            # Actualizar etiqueta
            self.lbl_caja_num.setText(f"Caja №:        [{caja_id:02d}]{hostname}  ({total_activos} PC(s) online)")
            
            # Efecto Destello (Flash LED Blanco a Verde estilo router)
            self.led_status.setStyleSheet("background-color: #FFFFFF; border-radius: 7px; border: 1.5px solid #34D399;")
            QTimer.singleShot(400, lambda: self.led_status.setStyleSheet(
                "background-color: #10B981; border-radius: 7px; border: 1.5px solid rgba(255,255,255,0.5);"
            ))
        except Exception:
            # Si falla la conexión a la base de datos o red, poner LED en rojo
            self.led_status.setStyleSheet("background-color: #EF4444; border-radius: 7px; border: 1.5px solid white;")
            try:
                caja_id = config.get("caja_id", 1)
                hostname = socket.gethostname().upper()
                self.lbl_caja_num.setText(f"Caja №:        [{caja_id:02d}]{hostname}  (Desconectado)")
            except Exception:
                self.lbl_caja_num.setText("Caja №:        Desconectado")

    def verificar_stock_minimo(self):
        try:
            # Productos donde stock es igual o menor al stock minimo, y minimo es mayor a 0
            query = "SELECT COUNT(*) FROM productos WHERE stock <= stock_minimo AND stock_minimo > 0"
            bajos = db_manager.execute_scalar(query) or 0
            
            if bajos > 0:
                self.lbl_stock_alert.setText(f"🔔 ALERTA DE INVENTARIO: Hay {bajos} productos con stock crítico/debajo del mínimo.")
                if self.stock_alert_bar.isHidden():
                    self.stock_alert_bar.show()
            else:
                if not self.stock_alert_bar.isHidden():
                    self.stock_alert_bar.hide()
        except Exception as e:
            logger.debug(f"Stock checker error: {e}")

    def verificar_autocierre(self):
        try:
            hora_target = config.get("cierre_auto_hora", "00:00")
            hora_actual = datetime.now().strftime("%H:%M")
            
            # Solo intentamos ejecutar si coincide el minuto exacto
            if hora_actual == hora_target:
                from src.services.caja_service import verificar_y_realizar_autocierre
                hizo_cierre, monto = verificar_y_realizar_autocierre()
                if hizo_cierre:
                    logger.info(f"Cierre automático ejecutado exitosamente a las {hora_actual}.")
                    self._agregar_al_ticket("> [SISTEMA] CIERRE AUTOMÁTICO EFECTUADO.", 0, 0, color="#10B981")
        except Exception as e:
            logger.error(f"Autoclose error: {e}")

    def refresh_terminal_data(self):
        """ 
        REFRESCO TOTAL (F11 Back): Actualiza precios de la tabla, ofertas y config. 
        Evita que el cajero use precios viejos tras una intervención de supervisor.
        """
        logger.info("Refrescando datos del terminal post-intervención...")
        # 1. Recargar Configuración (Por si cambiaron balanza, impresora, etc.)
        from src.config import config as _c
        _c._load_config() 
        
        # Recargar título y barra de estado dinámicamente
        self.refresh_terminal_title()
        self.refresh_status_bar()
        self._refresh_urgencia_stock_banner()
        
        # 2. Actualizar ítems en la tabla
        for i in range(self.tabla.rowCount()):
            p_id = self.tabla.item(i, 0).text()
            res = db_manager.execute_query("SELECT nombre, precio, cant_oferta, precio_oferta FROM productos WHERE id=?", (p_id,))
            if res:
                p = res[0]
                p_base = float(p['precio'])
                cant = float(self.tabla.item(i, 3).text())
                c_of = float(p['cant_oferta'] or 0)
                p_of = float(p['precio_oferta'] or 0)
                
                if c_of > 0 and p_of > 0 and cant >= c_of:
                    p_final = p_of
                    desc = (p_base - p_of) * cant
                    nombre = f"🔥 [OFERTA] {p['nombre']}"
                else:
                    p_final = p_base
                    desc = 0.0
                    nombre = p['nombre']
                
                self.tabla.item(i, 1).setText(nombre)
                self.tabla.item(i, 2).setText(fmt_moneda_sin_centavos(p_final))
                self.tabla.item(i, 4).setText(fmt_moneda_sin_centavos(desc))
                self.tabla.item(i, 5).setText(fmt_moneda_sin_centavos(cant * p_final))
                self._reaplicar_estilo_fila(i)
        
        self.actualizar_totales()
        if hasattr(self, 'txt_scan') and self.txt_scan:
            self.txt_scan.setFocus()

    def monitor_permanente_seguridad(self):
        """ Deprecado en favor de drawer_manager.check_status """
        pass

    def monitor_cajon_bloqueante(self, manual=False):
        """ Deprecado en favor de drawer_manager reactivo """
        pass

    def mostrar_alerta_perimetral(self, visible, modo="security"):
        """ Llama a la alerta global de la ventana principal con el modo especificado. """
        parent = self.window()
        if hasattr(parent, 'mostrar_alerta_perimetral'):
            parent.mostrar_alerta_perimetral(visible, modo=modo)
        
        # Efecto local en dashboard_frame solo en modo seguridad
        if visible and modo == "security":
            if not hasattr(self, '_orig_style'): self._orig_style = self.dashboard_frame.styleSheet()
            self.dashboard_frame.setStyleSheet("background-color: #FEE2E2; border: 5px solid #B91C1C; border-radius: 15px;")
        else:
            if hasattr(self, '_orig_style'): self.dashboard_frame.setStyleSheet(self._orig_style)

    def setup_ui(self):
        self.setStyleSheet("background-color: #F8FAFC; color: #333333; font-family: 'Inter', 'Segoe UI Variable', 'Segoe UI', sans-serif;")
        # Layout principal con márgenes para que nada toque los bordes ("el techo y el piso")
        # Layout principal con márgenes suaves
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(130)  # Much larger top header
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #3B82F6); 
                color: white; 
                border-radius: 12px;
            }
            QLabel { background: transparent; color: #F8FAFC; }
        """)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        col1 = QVBoxLayout(); col1.setSpacing(0)
        self.lbl_estado = QLabel("Estado:           MAESTRA")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.lbl_instalacion = QLabel("№ 0000-0000-0000")
        self.lbl_instalacion.setStyleSheet("font-weight: bold; font-size: 16px;")
        col1.addWidget(self.lbl_estado)
        col1.addWidget(self.lbl_instalacion)
        header_layout.addLayout(col1)
        
        header_layout.addSpacing(40)
        
        col2 = QVBoxLayout(); col2.setSpacing(0)
        
        # Fila para el indicador LED y el número de caja
        row_caja = QHBoxLayout()
        row_caja.setSpacing(8)
        row_caja.setContentsMargins(0, 0, 0, 0)
        
        # LED indicador circular (inicialmente verde)
        self.led_status = QLabel()
        self.led_status.setFixedSize(14, 14)
        self.led_status.setStyleSheet("background-color: #10B981; border-radius: 7px; border: 1.5px solid rgba(255,255,255,0.5);")
        row_caja.addWidget(self.led_status, 0, Qt.AlignVCenter)
        
        self.lbl_caja_num = QLabel("Caja №:        [01] SERVER")
        self.lbl_caja_num.setStyleSheet("font-weight: bold; font-size: 16px;")
        row_caja.addWidget(self.lbl_caja_num)
        row_caja.addStretch()
        
        col2.addLayout(row_caja)
        
        self.lbl_fecha = QLabel(f"Fecha:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.lbl_fecha.setStyleSheet("font-weight: bold; font-size: 16px;")
        col2.addWidget(self.lbl_fecha)
        header_layout.addLayout(col2)
        
        header_layout.addStretch()
        
        title = config.get('business_name', 'Punto de Venta [20.09.02]')
        self.lbl_terminal_title = QLabel(title)
        self._orig_title = title
        self.lbl_terminal_title.setStyleSheet("font-size: 26px; font-weight: bold;")
        header_layout.addWidget(self.lbl_terminal_title)
        self.main_layout.addWidget(self.header_frame)
        
        # --- BARRA DE ALERTA STOCK MÍNIMO ---
        self.stock_alert_bar = QFrame()
        self.stock_alert_bar.setFixedHeight(36)
        self.stock_alert_bar.setStyleSheet("background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 6px;")
        self.stock_alert_bar.hide()
        sa_lay = QHBoxLayout(self.stock_alert_bar)
        sa_lay.setContentsMargins(15, 0, 15, 0)
        self.lbl_stock_alert = QLabel("🔔 Alerta de Stock: Hay productos por debajo del mínimo")
        self.lbl_stock_alert.setStyleSheet("color: #D97706; font-weight: bold; font-size: 14px; border: none;")
        sa_lay.addWidget(self.lbl_stock_alert)
        self.main_layout.addWidget(self.stock_alert_bar)

        from src.shared.urgencia_stock_banner import UrgenciaStockBanner
        self.urgencia_stock_banner = UrgenciaStockBanner(
            self,
            "🚨 URGENCIA ACTIVA — Venta permitida SIN STOCK (desactívelo en Admin → Inventario)",
        )
        self.main_layout.addWidget(self.urgencia_stock_banner)
        self._refresh_urgencia_stock_banner()

        
        # Inicializar barra de estado con datos reales
        self.refresh_status_bar()

        # --- CENTRO (TABLA Y FOOTER JUNTOS) ---
        self.central_frame = QFrame()
        self.central_frame.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #CBD5E1;")
        central_layout = QVBoxLayout(self.central_frame)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # --- TABLA CENTRAL ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "DESCRIPCION PRODUCTO", "PRECIO", "CANT", "DES. TOTAL", "TOTAL"])
        self.tabla.setStyleSheet("""
            QTableWidget { 
                background-color: white;
                alternate-background-color: #F8FAFC;
                color: #1E293B; 
                gridline-color: transparent;
                border: none; 
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: 14px; 
                font-weight: 800; 
                selection-background-color: #EFF6FF;
                selection-color: #1E3A8A; 
                outline: none; /* Elimina el feo cuadro punteado nativo al seleccionar una celda */
            }
            QTableWidget::item {
                padding: 8px 15px; 
                border-bottom: 1px solid #E2E8F0;
            }
            QTableWidget::item:hover {
                background-color: #F1F5F9;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
                color: #1E3A8A;
                font-weight: 900;
            }
            QHeaderView::section { 
                background-color: #F8FAFC; 
                color: #475569; 
                border: none; 
                border-bottom: 3px solid #E2E8F0;
                padding: 16px 15px; 
                font-weight: 900; 
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed) # Bloquear columnas numéricas para evitar que Qt las exprima
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Solo la descripción se estira dinámicamente
        
        # Distribuir anchos de columna profesionales y bloqueados (Garantía Cero Truncamientos)
        self.tabla.setColumnWidth(0, 100) # ID / Barcode
        self.tabla.setColumnWidth(2, 150) # PRECIO
        self.tabla.setColumnWidth(3, 100) # CANT
        self.tabla.setColumnWidth(4, 150) # DES. TOTAL
        self.tabla.setColumnWidth(5, 200) # SUBTOTAL
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.installEventFilter(self) # BINDING INDUSTRIAL PARA ENTER EN LA TABLA
        self._nav_border_overlay = NavRowBorderOverlay(self.tabla)
        self.tabla.viewport().installEventFilter(self)
        self.tabla.verticalScrollBar().valueChanged.connect(lambda *_: self._sync_nav_border_overlay())
        self.tabla.horizontalScrollBar().valueChanged.connect(lambda *_: self._sync_nav_border_overlay())
        self.tabla.currentCellChanged.connect(self._on_tabla_nav_changed)
        self.tabla.itemSelectionChanged.connect(self._on_tabla_nav_row_only)
        self._nav_prev_row = -1
        central_layout.addWidget(self.tabla)
        
        self.main_layout.addWidget(self.central_frame, 2)

        # --- BOTTOM DASHBOARD ---
        self.dashboard_frame = QFrame()
        self.dashboard_frame.setFixedHeight(230)  # Drastically increase bottom panel height
        self.dashboard_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border: 1px solid #CBD5E1;")
        dash_layout = QHBoxLayout(self.dashboard_frame)
        dash_layout.setContentsMargins(10, 5, 10, 5)
        
        # F1-Barcode
        self.f1_box = QFrame()
        self.f1_box.setStyleSheet("border: none;")
        self.f1_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        f1_l = QVBoxLayout(self.f1_box)
        f1_l.setContentsMargins(5, 15, 5, 15)
        f1_l.setSpacing(0)
        
        self.txt_scan = QLineEdit()
        self.txt_scan.setPlaceholderText("🔍 Código o Producto (F1)...")
        self.txt_scan.setStyleSheet("""
            QLineEdit {
                background: white; border: 3px solid #3B82F6; border-radius: 12px; 
                color: #1E3A8A; font-size: 24px; padding: 10px; font-weight: 900;
            }
        """)
        
        # Sombra sutil (elevación nivel 2) — no glow neón
        self._scan_shadow = QGraphicsDropShadowEffect(self.txt_scan)
        self._scan_shadow.setOffset(0, 4)
        self._scan_shadow.setBlurRadius(10)
        self._scan_shadow.setColor(QColor(0, 0, 0, 56))  # ~22% opacidad
        self.txt_scan.setGraphicsEffect(self._scan_shadow)

        self.txt_scan.textChanged.connect(self.actualizar_busqueda)
        self.txt_scan.returnPressed.connect(self.procesar_scan)
        
        f1_l.addWidget(self.txt_scan)
        dash_layout.addWidget(self.f1_box, stretch=2)
        
        # Overlay de Búsqueda
        self.list_results = QListWidget(self)
        self.list_results.setStyleSheet("background: white; border: 2px solid #437EE8; color: #333333; font-size: 22px; font-weight: bold;")
        self.list_results.itemClicked.connect(self.seleccionar_item_busqueda)
        self.list_results.installEventFilter(self)
        self.list_results.hide()
        
        # Cantidad (Oculto a petición para dar más espacio al total)
        self.lbl_cant_val = QLabel("0")
        self.lbl_cant_val.hide()
        # cant_box = QVBoxLayout()
        # cant_box.setSpacing(0)
        # lbl_cant_tit = QLabel("Cantidad")
        # lbl_cant_tit.setStyleSheet("color: #64748B; font-size: 24px; font-weight: bold; border: none;")
        # self.lbl_cant_val.setStyleSheet("font-size: 70px; color: #1C2E85; font-weight: bold; border: none;")
        # cant_box.addWidget(lbl_cant_tit)
        # cant_box.addWidget(self.lbl_cant_val)
        dash_layout.addStretch()
        
        # Ahorro Label (Contenedor para la animación de Ahorro / Descuento)
        self.lbl_ahorro_val = QLabel("")
        self.lbl_ahorro_val.setStyleSheet("font-size: 42px; color: #FF4500; font-weight: 900; border: none;")
        self.lbl_ahorro_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.ahorro_glow = QGraphicsDropShadowEffect(self.lbl_ahorro_val)
        self.ahorro_glow.setBlurRadius(20)
        self.ahorro_glow.setColor(QColor(255, 69, 0, 150)) # Brillo naranja vibrante
        self.ahorro_glow.setOffset(0, 0)
        self.lbl_ahorro_val.setGraphicsEffect(self.ahorro_glow)
        
        self.lbl_ahorro_val.hide()

        self.lbl_total_val = QLabel("0")
        self.lbl_total_val.setStyleSheet("font-size: 55px; color: #059669; font-weight: 900; border: none;")
        self.lbl_total_val.setAlignment(Qt.AlignRight)
        
        # Agrupar Ahorro y Total lado a lado en un contenedor horizontal perfectamente centrado verticalmente
        self.totales_container = QHBoxLayout()
        self.totales_container.setSpacing(35)
        self.totales_container.addWidget(self.lbl_total_val, alignment=Qt.AlignVCenter)
        self.totales_container.addWidget(self.lbl_ahorro_val, alignment=Qt.AlignVCenter)
        dash_layout.addLayout(self.totales_container, stretch=3)
        
        # Sidebar Resumen
        self.side_box = QFrame()
        self.side_box.setMinimumWidth(120)
        self.side_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.side_box.setStyleSheet("""
            QFrame {
                background: #f8fafc; 
                border: 1px solid #e2e8f0; 
                border-radius: 12px;
            }
            QLabel { border: none; background: transparent; }
        """)
        sl = QVBoxLayout(self.side_box)
        sl.setContentsMargins(15, 10, 15, 10)
        sl.setSpacing(6)

        self.lbl_side_cant_t, self.lbl_side_cant = self._build_side_summary_row(sl, "CANTIDAD")
        self.lbl_side_cant.setText("0")
        self.lbl_side_total_t, self.lbl_side_total = self._build_side_summary_row(sl, "TOTAL VENTA")
        self.lbl_side_total.setText("0")
        self.lbl_side_ahorro_t, self.lbl_side_ahorro = self._build_side_summary_row(sl, "AHORRO OFER")
        self.lbl_side_ahorro.setText("0")
        self.lbl_side_ahorro_t.hide()
        self.lbl_side_ahorro.hide()
        self.lbl_side_pagos_t, self.lbl_side_pagos = self._build_side_summary_row(sl, "PAGOS")
        self.lbl_side_pagos.setText("0")
        self.lbl_side_cambio_t, self.lbl_side_cambio = self._build_side_summary_row(sl, "CAMBIO")
        self.lbl_side_cambio.setText("0")

        self._style_side_labels(cambio_highlight=False)
        
        dash_layout.addWidget(self.side_box, stretch=1)
        
        self.en_venta = False
        self.main_layout.addWidget(self.dashboard_frame)
        
        # --- BARRA DE ESTADO / COMANDOS (EL PISO) ---
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(55) # Taller status bar for touch screens
        self.status_bar.setStyleSheet("background: #0F172A; border-top: 1px solid #334155;")
        sl = QHBoxLayout(self.status_bar); sl.setContentsMargins(15, 0, 5, 0)
        
        if HAS_KEYBOARD:
            self.btn_teclado = QPushButton("⌨️ TECLADO")
            self.btn_teclado.setFixedHeight(40)
            self.btn_teclado.setCursor(Qt.PointingHandCursor)
            self.btn_teclado.setFocusPolicy(Qt.NoFocus)
            self.btn_teclado.setStyleSheet("""
                QPushButton {
                    background: #1E293B; color: #F8FAFC; border-radius: 5px;
                    font-size: 12px; font-weight: bold; border: 1px solid #334155;
                    padding: 0px 12px;
                }
                QPushButton:hover { background: #334155; border-color: #475569; }
            """)
            self.btn_teclado.clicked.connect(self.toggle_keyboard)
            sl.addWidget(self.btn_teclado)
            sl.addSpacing(10)

        self.btn_theme = QPushButton()
        self.btn_theme.setFixedHeight(40)
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setFocusPolicy(Qt.NoFocus)
        self.btn_theme.setStyleSheet("""
            QPushButton {
                background: #1E293B; color: #F8FAFC; border-radius: 5px;
                font-size: 12px; font-weight: bold; border: 1px solid #334155;
                padding: 0px 12px;
            }
            QPushButton:hover { background: #334155; border-color: #475569; }
        """)
        self.btn_theme.clicked.connect(self.toggle_theme)
        sl.addWidget(self.btn_theme)
        sl.addSpacing(10)

        from src.updater.github_updater import get_local_version
        v_local = get_local_version()
        self.lbl_version = QLabel(f"🚀 COBRO FACIL {v_local}")
        self.lbl_version.setStyleSheet("color: #10B981; font-weight: 900; font-size: 11px; letter-spacing: 1px; border: none;")
        self.lbl_version.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sl.addWidget(self.lbl_version)
        sl.addSpacing(10)
        sl.addStretch(1)

        self.btn_espera = QPushButton("⏳ 0 Espera")
        self.btn_espera.setFixedHeight(40)
        self.btn_espera.setCursor(Qt.PointingHandCursor)
        self.btn_espera.setFocusPolicy(Qt.NoFocus)
        self.btn_espera.setToolTip("Poner ticket en espera / Recuperar ticket (swap)")
        self.btn_espera.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #000000; border-radius: 5px;
                font-size: 13px; font-weight: 900; border: 1px solid #CBD5E1;
                padding: 0px 15px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        self.btn_espera.clicked.connect(self._swap_ticket_espera)
        sl.addWidget(self.btn_espera)

        sl.addStretch(1)

        self._shortcuts_scroll = QScrollArea()
        self._shortcuts_scroll.setWidgetResizable(False)
        self._shortcuts_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._shortcuts_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._shortcuts_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._shortcuts_scroll.setFixedHeight(44)
        self._shortcuts_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._hints_widget = QWidget()
        self._hints_widget.setStyleSheet("background: transparent; border: none;")
        hints_layout = QHBoxLayout(self._hints_widget)
        hints_layout.setSpacing(8)
        hints_layout.setContentsMargins(0, 0, 0, 0)
        self._hints_layout = hints_layout

        # Icono de teclado eliminado a petición del usuario
        self._shortcut_btn_base_style = """
            QPushButton {{
                background: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                font-size: {font_px}px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: #F1F5F9;
                border-color: #94A3B8;
            }}
            QPushButton:pressed {{
                background: #CBD5E1;
            }}
        """

        hints = [
            ("F1", self._do_busqueda, "Buscar Producto (F1)"),
            ("F3", self.abrir_historial_dia, "Ver Historial del Día (F3)"),
            ("F12", self.finalizar_venta, "Cobrar / Pagar Venta (F12)"),
            ("F5", self.abrir_retiro_efectivo, "Retiro de Efectivo (F5)"),
            ("F6", self.abrir_ingreso_efectivo, "Ingreso de Efectivo (F6)"),
            ("F7", self._leer_bascula, "Leer Báscula (F7)"),
            ("F8", self.bloquear_terminal, "Bloquear Terminal (F8)"),
            ("F4", self.abrir_cierre_caja, "Cierre de Turno / Caja (F4)"),
            ("F11", self.llamar_supervisor, "Llamar Supervisor (F11)"),
        ]

        self.shortcut_buttons = []
        for text, func, tooltip in hints:
            btn = QPushButton(text)
            btn.setStyleSheet(self._shortcut_btn_base_style.format(font_px=13))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setFixedSize(45, 40)
            btn.setToolTip(tooltip)
            btn.clicked.connect(func)
            hints_layout.addWidget(btn)
            self.shortcut_buttons.append(btn)

        self._shortcuts_scroll.setWidget(self._hints_widget)
        sl.addWidget(self._shortcuts_scroll, stretch=2)
        sl.addSpacing(10)
        
        # Botón Candado
        self.btn_candado = QPushButton("🔒")
        self.btn_candado.setFixedSize(40, 40) # Square size 40x40
        self.btn_candado.setToolTip("Bloquear terminal (F8)")
        self.btn_candado.setCursor(Qt.PointingHandCursor)
        self.btn_candado.setStyleSheet("""
            QPushButton {
                background: #1E3A8A; color: white; border-radius: 5px;
                font-size: 14px; font-weight: bold; border: 1px solid #3B82F6;
            }
            QPushButton:hover { background: #EF4444; border-color: #EF4444; }
        """)
        self.btn_candado.clicked.connect(self.bloquear_terminal)
        self.btn_candado.setFocusPolicy(Qt.NoFocus)
        sl.addWidget(self.btn_candado)
        
        # Botón Manual Chatbot (Adorno)
        self.btn_chatbot = QPushButton("🤖")
        self.btn_chatbot.setFixedSize(40, 40) # Square size 40x40
        self.btn_chatbot.setToolTip("Asistente Virtual")
        self.btn_chatbot.setCursor(Qt.PointingHandCursor)
        self.btn_chatbot.setStyleSheet("""
            QPushButton {
                background: #10B981; color: white; border-radius: 5px;
                font-size: 14px; font-weight: bold; border: 1px solid #059669;
            }
            QPushButton:hover { background: #059669; }
        """)
        self.btn_chatbot.clicked.connect(self.toggle_chatbot)
        self.btn_chatbot.setFocusPolicy(Qt.NoFocus)
        sl.addWidget(self.btn_chatbot)
        
        self.main_layout.addWidget(self.status_bar)
        QTimer.singleShot(0, self._apply_screen_layout)
        self.txt_scan.setFocus()
        QTimer.singleShot(500, self.txt_scan.setFocus) # Asegurar foco inicial
        self.txt_scan.installEventFilter(self) # Para monitoreo PRO
        
    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key_F1: self._do_busqueda()
        elif k == Qt.Key_F3: self.abrir_historial_dia()
        elif k == Qt.Key_F12: self.finalizar_venta()
        elif k == Qt.Key_F5: self.abrir_retiro_efectivo()
        elif k == Qt.Key_F6: self.abrir_ingreso_efectivo()
        elif k == Qt.Key_F7: self._leer_bascula()
        elif k == Qt.Key_F8: self.bloquear_terminal()
        elif k == Qt.Key_F4: self.abrir_cierre_caja()
        elif k == Qt.Key_F11: self.llamar_supervisor()
        elif k == Qt.Key_Escape:
            if getattr(self, 'list_results', None) is not None and not self.list_results.isHidden():
                self.list_results.hide()
            self.txt_scan.setFocus()

    def toggle_chatbot(self):
        self.request_chatbot_toggle.emit()
        self.txt_scan.setFocus()

    def llamar_supervisor(self):
        main_win = self.window()
        if main_win and hasattr(main_win, 'handle_f11_global'):
            main_win.handle_f11_global()

    def paintEvent(self, event):
        from PyQt6.QtWidgets import QStyle, QStyleOption
        from PyQt6.QtGui import QPainter
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

    def hideEvent(self, event):
        super().hideEvent(event)
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(b"HIDE", ("127.0.0.1", 45680))
            sock.close()
        except Exception:
            pass
            
    def _leer_bascula(self):
        try:
            import serial
            import re
            # Intentar abrir el puerto COM1 (o el configurado)
            puerto = config.get("puerto_bascula", "COM1")
            ser = serial.Serial(puerto, 9600, timeout=1)
            # Solicitar peso (depende de la bascula, normalmente enviando una letra como 'P' o Enter)
            ser.write(b'P\r\n')
            time.sleep(0.2)
            respuesta = ser.readline().decode('ascii', errors='ignore').strip()
            ser.close()
            
            if respuesta:
                # Extraer solo numeros
                peso_match = re.search(r'([0-9]+\.[0-9]+)', respuesta)
                if peso_match:
                    peso = peso_match.group(1)
                    # Insertar peso en la caja de multiplicador
                    self.txt_scan.setText(f"{peso}*")
                    QMessageBox.information(self, "Báscula", f"Peso leído: {peso} kg")
                else:
                    QMessageBox.warning(self, "Báscula", f"Lectura no reconocida: {respuesta}")
            else:
                # Simulador si no hay respuesta real
                peso_simulado = "1.250"
                self.txt_scan.setText(f"{peso_simulado}*")
                QMessageBox.information(self, "Báscula (Simulador)", f"Báscula no encontrada en {puerto}.\nSe simuló un peso de {peso_simulado} kg para pruebas.")
        except ImportError:
            QMessageBox.critical(self, "Error", "Falta instalar pyserial (pip install pyserial).")
        except Exception as e:
            # Simulador de falla segura
            peso_simulado = "0.750"
            self.txt_scan.setText(f"{peso_simulado}*")
            QMessageBox.information(self, "Báscula (Simulador)", f"No se detectó báscula física en el puerto configurado.\nSe simuló un peso de {peso_simulado} kg para pruebas.\n\nDetalle técnico: {e}")

        # Conectar detector de foco para teclado virtual automático (estilo celular)
        if HAS_KEYBOARD:
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().focusChanged.connect(self.on_focus_changed)

    def mousePressEvent(self, event):
        # Al hacer click en cualquier parte, el cursor vuelve al buscador y se oculta la lista
        if getattr(self, 'list_results', None) is not None and not self.list_results.isHidden():
            self.list_results.hide()
        if getattr(self, 'txt_scan', None) is not None:
            self.txt_scan.setFocus()
        super().mousePressEvent(event)

    def toggle_theme(self):
        current = config.get("theme", "light")
        new_theme = "dark" if current == "light" else "light"
        config.set("theme", new_theme)
        
        # OPTIMIZACION: Pausar el renderizado mientras se inyectan multiples hojas de estilo
        self.setUpdatesEnabled(False)
        try:
            self.apply_theme()
            if HAS_KEYBOARD and hasattr(self, 'teclado_virtual'):
                if hasattr(self.teclado_virtual, 'apply_theme'):
                    self.teclado_virtual.apply_theme()
        finally:
            self.setUpdatesEnabled(True)
            self.repaint()

    def apply_theme(self):
        theme = config.get("theme", "light")
        if hasattr(self, 'btn_theme'):
            self.btn_theme.setText("☀️ TEMAS" if theme == "dark" else "🌙 TEMAS")
        
        # Style QToolTip globally to be always dark with white text (highest readability, bypasses native OS theme quirks)
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet("""
                QToolTip {
                    background-color: #1E293B;
                    color: #FFFFFF;
                    border: 1px solid #334155;
                    font-family: 'Inter', 'Segoe UI Variable', 'Segoe UI', sans-serif;
                    padding: 5px;
                    border-radius: 4px;
                }
            """)

        if theme == "dark":
            self.setStyleSheet("""
                Paso5Terminal {
                    background-color: #0F172A; 
                    color: #F8FAFC; 
                    font-family: 'Inter', 'Segoe UI Variable', 'Segoe UI', sans-serif;
                }
            """)
            if hasattr(self, 'central_frame'):
                self.central_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; border: 1px solid #334155;")
            if hasattr(self, 'tabla'):
                self.tabla.setStyleSheet("""
                    QTableWidget { 
                        background-color: #1E293B;
                        alternate-background-color: #0F172A;
                        color: #F8FAFC; 
                        gridline-color: transparent;
                        border: none; 
                        border-top-left-radius: 12px;
                        border-top-right-radius: 12px;
                        font-size: 19px; 
                        font-weight: 800; 
                        selection-background-color: #EFF6FF;
                        selection-color: #1E3A8A; 
                        outline: none;
                    }
                    QTableWidget::item {
                        padding: 8px 15px; 
                        border-bottom: 1px solid #334155;
                    }
                    QTableWidget::item:hover {
                        background-color: #334155;
                    }
                    QTableWidget::item:selected {
                        background-color: #EFF6FF;
                        color: #1E3A8A;
                        font-weight: 900;
                    }
                    QHeaderView::section { 
                        background-color: #0F172A; 
                        color: #94A3B8; 
                        border: none; 
                        border-bottom: 3px solid #334155;
                        padding: 16px 15px; 
                        font-weight: 900; 
                        font-size: 13px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }
                """)
            if hasattr(self, 'dashboard_frame'):
                self.dashboard_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; border: 1px solid #334155;")
            if hasattr(self, 'txt_scan') and self.txt_scan is not None:
                self.txt_scan.setStyleSheet("""
                    QLineEdit {
                        background: #0F172A;
                        border: 2px solid #334155;
                        border-radius: 8px;
                        padding: 10px 15px;
                        font-size: 26px;
                        font-weight: bold;
                        color: #38BDF8;
                    }
                    QLineEdit:focus {
                        border: 2px solid #3B82F6;
                    }
                """)
            if hasattr(self, 'list_results') and self.list_results is not None:
                self.list_results.setStyleSheet("background: #0F172A; border: 2px solid #38BDF8; color: #F8FAFC; font-size: 22px; font-weight: bold;")
            if hasattr(self, 'lbl_ahorro_val'):
                self.lbl_ahorro_val.setStyleSheet("font-size: 42px; color: #F43F5E; font-weight: 900; border: none; background: transparent;")
            if hasattr(self, 'lbl_total_val'):
                self.lbl_total_val.setStyleSheet("font-size: 75px; color: #34D399; font-weight: 900; border: none; background: transparent;")
            if hasattr(self, 'side_box'):
                self.side_box.setStyleSheet("""
                    QFrame {
                        background-color: #0F172A;
                        border: 1px solid #334155;
                        border-radius: 12px;
                    }
                    QLabel { border: none; background: transparent; }
                """)
            if hasattr(self, 'status_bar'):
                self.status_bar.setStyleSheet("background: #0F172A; border-top: 1px solid #334155;")
            btn_control_dark = """
                QPushButton {
                    background: #1E293B; color: #F8FAFC; border-radius: 5px;
                    font-size: 12px; font-weight: bold; border: 1px solid #334155;
                    padding: 0px 12px;
                }
                QPushButton:hover { background: #334155; border-color: #475569; }
            """
            if hasattr(self, 'btn_teclado'):
                self.btn_teclado.setStyleSheet(btn_control_dark)
            if hasattr(self, 'btn_theme'):
                self.btn_theme.setStyleSheet(btn_control_dark)
            if hasattr(self, 'icon_lbl'):
                self.icon_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; border: none; background: transparent;")
            btn_style_dark = """
                QPushButton {
                    background: #1E293B; 
                    color: #F8FAFC; 
                    border: 1px solid #334155; 
                    border-radius: 5px;
                    font-size: 13px; 
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover { 
                    background: #334155; 
                    border-color: #475569; 
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: #0F172A;
                }
            """
            if hasattr(self, 'shortcut_buttons'):
                for btn in self.shortcut_buttons:
                    btn.setStyleSheet(btn_style_dark)
        else:
            self.setStyleSheet("""
                Paso5Terminal {
                    background-color: #F8FAFC; 
                    color: #333333; 
                    font-family: 'Inter', 'Segoe UI Variable', 'Segoe UI', sans-serif;
                }
            """)
            if hasattr(self, 'central_frame'):
                self.central_frame.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #CBD5E1;")
            if hasattr(self, 'tabla'):
                self.tabla.setStyleSheet("""
                    QTableWidget { 
                        background-color: white;
                        alternate-background-color: #F8FAFC;
                        color: #1E293B; 
                        gridline-color: transparent;
                        border: none; 
                        border-top-left-radius: 12px;
                        border-top-right-radius: 12px;
                        font-size: 19px; 
                        font-weight: 800; 
                        selection-background-color: #EFF6FF;
                        selection-color: #1E3A8A; 
                        outline: none;
                    }
                    QTableWidget::item {
                        padding: 8px 15px; 
                        border-bottom: 1px solid #E2E8F0;
                    }
                    QTableWidget::item:hover {
                        background-color: #F1F5F9;
                    }
                    QTableWidget::item:selected {
                        background-color: #EFF6FF;
                        color: #1E3A8A;
                        font-weight: 900;
                    }
                    QHeaderView::section { 
                        background-color: #F8FAFC; 
                        color: #475569; 
                        border: none; 
                        border-bottom: 3px solid #E2E8F0;
                        padding: 16px 15px; 
                        font-weight: 900; 
                        font-size: 13px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }
                """)
            if hasattr(self, 'dashboard_frame'):
                self.dashboard_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border: 1px solid #CBD5E1;")
            if hasattr(self, 'txt_scan') and self.txt_scan is not None:
                self.txt_scan.setStyleSheet("""
                    QLineEdit {
                        background: #F1F5F9;
                        border: 2px solid #CBD5E1;
                        border-radius: 8px;
                        padding: 10px 15px;
                        font-size: 26px;
                        font-weight: bold;
                        color: #1E293B;
                    }
                    QLineEdit:focus {
                        border: 2px solid #3b82f6;
                    }
                """)
            if hasattr(self, 'list_results') and self.list_results is not None:
                self.list_results.setStyleSheet("background: white; border: 2px solid #437EE8; color: #333333; font-size: 22px; font-weight: bold;")
            if hasattr(self, 'lbl_ahorro_val'):
                self.lbl_ahorro_val.setStyleSheet("font-size: 42px; color: #FF4500; font-weight: 900; border: none; background: transparent;")
            if hasattr(self, 'lbl_total_val'):
                self.lbl_total_val.setStyleSheet("font-size: 75px; color: #059669; font-weight: 900; border: none; background: transparent;")
            if hasattr(self, 'side_box'):
                self.side_box.setStyleSheet("""
                    QFrame {
                        background: #f8fafc; 
                        border: 1px solid #e2e8f0; 
                        border-radius: 12px;
                    }
                    QLabel { border: none; background: transparent; }
                """)
            if hasattr(self, 'status_bar'):
                self.status_bar.setStyleSheet("background: #E2E8F0; border-top: 1px solid #CBD5E1;")
            btn_control_light = """
                QPushButton {
                    background: #FFFFFF; color: #0F172A; border-radius: 5px;
                    font-size: 12px; font-weight: bold; border: 1px solid #CBD5E1;
                    padding: 0px 12px;
                }
                QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }
            """
            if hasattr(self, 'btn_teclado'):
                self.btn_teclado.setStyleSheet(btn_control_light)
            if hasattr(self, 'btn_theme'):
                self.btn_theme.setStyleSheet(btn_control_light)
            if hasattr(self, 'icon_lbl'):
                self.icon_lbl.setStyleSheet("color: #475569; font-size: 11px; border: none; background: transparent;")
            btn_style_light = """
                QPushButton {
                    background: #FFFFFF; 
                    color: #0F172A; 
                    border: 1px solid #CBD5E1; 
                    border-radius: 5px;
                    font-size: 13px; 
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover { 
                    background: #F1F5F9; 
                    border-color: #94A3B8; 
                    color: #0F172A;
                }
                QPushButton:pressed {
                    background: #CBD5E1;
                }
            """
            if hasattr(self, 'shortcut_buttons'):
                for btn in self.shortcut_buttons:
                    btn.setStyleSheet(btn_style_light)

        if hasattr(self, 'lbl_side_cant'):
            self._style_side_labels(cambio_highlight=False)

    def toggle_keyboard(self):
        if not HAS_KEYBOARD:
            return
        active_win = self.window() or self
        if not hasattr(self, 'teclado_virtual'):
            self.teclado_virtual = VirtualKeyboard(active_win)
        elif self.teclado_virtual.parent() != active_win:
            self.teclado_virtual.setParent(active_win)
            self.teclado_virtual.setWindowFlags(
                Qt.Tool | 
                Qt.FramelessWindowHint | 
                Qt.WindowStaysOnTopHint | 
                Qt.WindowDoesNotAcceptFocus
            )
            
        if self.teclado_virtual.isVisible():
            self.teclado_virtual.hide()
        else:
            self.teclado_virtual.reposition_keyboard()
            self.teclado_virtual.show()

    def hideEvent(self, event):
        if HAS_KEYBOARD and hasattr(self, 'teclado_virtual'):
            self.teclado_virtual.hide()
        super().hideEvent(event)

    def on_focus_changed(self, old_widget, new_widget):
        if not HAS_KEYBOARD:
            return
            
        from src.config import config
        if not config.get("auto_virtual_keyboard", True):
            return
            
        # Sanitizar referencia de teclado virtual si el objeto C++ subyacente fue eliminado
        if hasattr(self, 'teclado_virtual') and self.teclado_virtual is not None:
            try:
                self.teclado_virtual.parent()
            except RuntimeError:
                self.teclado_virtual = None
                
        # Si la terminal de venta principal no está visible, ocultar y retornar
        if not self.isVisible():
            if getattr(self, 'teclado_virtual', None) is not None:
                self.teclado_virtual.hide()
            return
            
        from PyQt6.QtWidgets import QLineEdit, QApplication
        from PyQt6.QtCore import Qt
        
        # Si el foco entra a una caja de texto (QLineEdit)
        if new_widget and isinstance(new_widget, QLineEdit):
            # 1. Protección Panel Admin: no desplegar teclado virtual en formularios de administración
            parent = new_widget.parent()
            while parent:
                class_name = parent.__class__.__name__.lower()
                if 'admin' in class_name:
                    if getattr(self, 'teclado_virtual', None) is not None:
                        self.teclado_virtual.hide()
                    return
                parent = parent.parent()
                
            # 1.b Protección Paso 6 Cobro: el diálogo de cobro tiene el teclado incrustado directamente.
            is_paso6 = False
            parent = new_widget.parent()
            while parent:
                if parent.__class__.__name__ == 'Paso6Cobro':
                    is_paso6 = True
                    break
                parent = parent.parent()
            if is_paso6:
                if getattr(self, 'teclado_virtual', None) is not None:
                    self.teclado_virtual.hide()
                return

            active_win = new_widget.window()
            if not active_win:
                active_win = self.window()
                
            # 2. Protección Cambio de Ventana: ocultar antes si la ventana de destino cambió
            # Esto previene congelamientos y asegura que la nueva ventana inicie con un teclado limpio
            if getattr(self, 'teclado_virtual', None) is not None and self.teclado_virtual.isVisible():
                if self.teclado_virtual.parent() != active_win:
                    self.teclado_virtual.hide()
                    
            if getattr(self, 'teclado_virtual', None) is None:
                self.teclado_virtual = VirtualKeyboard(active_win)
            elif self.teclado_virtual.parent() != active_win:
                self.teclado_virtual.setParent(active_win)
                self.teclado_virtual.setWindowFlags(
                    Qt.Tool | 
                    Qt.FramelessWindowHint | 
                    Qt.WindowStaysOnTopHint | 
                    Qt.WindowDoesNotAcceptFocus
                )
                
            # En el buscador principal usamos layout alfabético por defecto (abc)
            self.teclado_virtual.set_layout_mode("abc")
            self.teclado_virtual.reposition_keyboard()
            self.teclado_virtual.show()
        else:
            # Si el foco cambia a cualquier otra cosa, ocultamos
            if getattr(self, 'teclado_virtual', None) is not None and self.teclado_virtual.isVisible():
                self.teclado_virtual.hide()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        
        if getattr(self, 'list_results', None) is not None and obj == self.list_results:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Up and self.list_results.currentRow() == 0:
                    self.txt_scan.setFocus()
                    return True
                elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    self.seleccionar_item_busqueda()
                    return True

        if getattr(self, 'txt_scan', None) is not None and obj == self.txt_scan:
            # INTERCEPTAR TECLAS DE FUNCIÓN: el QLineEdit consume los KeyPress
            # antes de que lleguen al keyPressEvent del widget padre.
            # Los capturamos aquí para garantizar que siempre funcionen.
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key == Qt.Key_F4:
                    self.abrir_cierre_caja()
                    return True  # Consumir el evento, no propagarlo
                elif key == Qt.Key_F3:
                    self.abrir_historial_dia()
                    return True
                elif key == Qt.Key_F12:
                    self.finalizar_venta()
                    return True
                elif key == Qt.Key_F1:
                    self.txt_scan.selectAll()
                    return True
                elif key == Qt.Key_F8:
                    self.bloquear_terminal()
                    return True
                elif key == Qt.Key_F5:
                    self.abrir_retiro_efectivo()
                    return True
                elif key == Qt.Key_F6:
                    self.abrir_ingreso_efectivo()
                    return True
                elif key == Qt.Key_Escape:
                    self.txt_scan.clear()
                    self.list_results.hide()
                    return True
                elif key == Qt.Key_Down:
                    if not self.list_results.isHidden() and self.list_results.count() > 0:
                        self.list_results.setFocus()
                        self.list_results.setCurrentRow(0)
                        return True
                    elif self.tabla.rowCount() > 0:
                        self.tabla.setFocus()
                        self.tabla.selectRow(self.tabla.rowCount() - 1)
                        self.tabla.setCurrentCell(self.tabla.rowCount() - 1, 3)
                        QTimer.singleShot(0, self._on_tabla_nav_row_only)
                        return True
                elif key == Qt.Key_Up:
                    if self.tabla.rowCount() > 0:
                        self.tabla.setFocus()
                        self.tabla.selectRow(self.tabla.rowCount() - 1)
                        self.tabla.setCurrentCell(self.tabla.rowCount() - 1, 3)
                        QTimer.singleShot(0, self._on_tabla_nav_row_only)
                        return True
                elif key in (Qt.Key_Return, Qt.Key_Enter):
                    # Si la lista de resultados está desplegada, procesamos el ítem seleccionado directamente
                    if not self.list_results.isHidden() and self.list_results.currentRow() >= 0:
                        self.seleccionar_item_busqueda()
                        return True
                    # Si el buscador está totalmente vacío, iniciar cobro como alternativa a F4
                    if not self.txt_scan.text().strip():
                        self.finalizar_venta()
                        return True
                    # De lo contrario, no lo consumimos para que siga el flujo natural a procesar_scan o al keyPressEvent del QLineEdit

            # GUARDIA DE FOCO: Si algo intenta quitarle el foco al buscador, lo devolvemos
            elif event.type() == QEvent.FocusOut:
                # CRÍTICO: Si el terminal no está visible (ej: estamos en IA Boss), no forzamos el foco
                if not self.isVisible():
                    return super().eventFilter(obj, event)
                # Solo permitimos perder foco hacia la lista de resultados o la tabla (navegación)
                if not (self.list_results.hasFocus() or self.tabla.hasFocus()):
                    QTimer.singleShot(50, lambda: getattr(self, 'txt_scan', None) is not None and self.txt_scan.setFocus())

        elif obj == self.tabla:
            if event.type() == QEvent.FocusOut:
                QTimer.singleShot(0, self._sync_nav_border_overlay)
            elif event.type() == QEvent.FocusIn:
                QTimer.singleShot(0, self._sync_nav_border_overlay)
            elif event.type() == QEvent.KeyPress:
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    row = self.tabla.currentRow()
                    if row != -1:
                        nombre = self.tabla.item(row, 1).text()
                        cant_actual = float(self.tabla.item(row, 3).text())
                        
                        dlg = DialogoEditarCantidad(cant_actual, nombre, self)
                        if qt_exec(dlg):
                            new_cant = dlg.get_value()
                            self.tabla.item(row, 3).setText(
                                f"{new_cant:.2f}" if new_cant % 1 != 0 else f"{int(new_cant)}"
                            )
                            
                            # Verificación dinámica de ofertas al ingresar con el Enter
                            p_id = self.tabla.item(row, 0).text()
                            res_of = db_manager.execute_query("SELECT precio, cant_oferta, precio_oferta FROM productos WHERE id=?", (p_id,))
                            if res_of and p_id != "000":
                                p_base = float(res_of[0]['precio'])
                                c_of = float(res_of[0]['cant_oferta'] or 0.0)
                                p_of = float(res_of[0]['precio_oferta'] or 0.0)
                                
                                if c_of > 0 and p_of > 0 and new_cant >= c_of:
                                    p_ap = p_of
                                    desc_t = (p_base - p_of) * new_cant
                                    nombre_txt = self.tabla.item(row, 1).text()
                                    if "🔥 [OFERTA]" not in nombre_txt:
                                        self.tabla.item(row, 1).setText(f"🔥 [OFERTA] {nombre_txt}")
                                else:
                                    p_ap = p_base
                                    desc_t = 0.0
                                    nombre_txt = self.tabla.item(row, 1).text()
                                    if "🔥 [OFERTA]" in nombre_txt:
                                        clean_name = nombre_txt.replace("🔥 [OFERTA] ", "")
                                        self.tabla.item(row, 1).setText(clean_name)
                                        
                                self.tabla.item(row, 2).setText(fmt_moneda_sin_centavos(p_ap))
                                self.tabla.item(row, 4).setText(fmt_moneda_sin_centavos(desc_t))
                                p_unit = p_ap
                            else:
                                p_unit = parse_float_safe(self.tabla.item(row, 2).text())
                            
                            # Actualizar Subtotal
                            self.tabla.item(row, 5).setText(fmt_moneda_sin_centavos(new_cant * p_unit))
                            self._reaplicar_estilo_fila(row)
                            self.actualizar_totales()
                        
                        QTimer.singleShot(50, self.txt_scan.setFocus)
                    return True # Consumido incondicionalmente
                elif event.key() == Qt.Key_Delete:
                    row = self.tabla.currentRow()
                    if row != -1:
                        dlg = DialogoAtencion(self)
                        if qt_exec(dlg):
                            self.tabla.removeRow(row)
                            self.actualizar_totales()
                        QTimer.singleShot(50, self.txt_scan.setFocus)
                    return True

        elif obj is self.tabla.viewport():
            if event.type() == QEvent.Resize:
                QTimer.singleShot(0, self._sync_nav_border_overlay)

        return super().eventFilter(obj, event)

    def flash_feedback(self, success=True):
        color = "#10B981" if success else "#EF4444"
        original_style = self.header_frame.styleSheet()
        self.header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color}; 
                color: white; 
                border-radius: 8px;
            }}
            QLabel {{ background: transparent; }}
        """)
        self.dashboard_frame.setStyleSheet(f"background-color: white; border: 4px solid {color}; border-radius: 8px;")
        
        def reset_style():
            self.header_frame.setStyleSheet(original_style)
            self.dashboard_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border: 1px solid #CBD5E1;")
            
        QTimer.singleShot(10000, reset_style) # Duración extendida a 10 segundos

    def bloquear_terminal(self):
        """Bloquea la terminal. Al desbloquear, el cajero seleccionado queda activo."""
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(15)
        self.setGraphicsEffect(blur_effect)
        
        dlg = DialogoCandado(parent=self)
        qt_exec(dlg)   # Si no se desbloquea, la terminal queda bloqueada
        
        self.setGraphicsEffect(None)

        # Actualizar barra de estado según el cajero activo
        self._actualizar_barra_cajero()
        QTimer.singleShot(50, self.txt_scan.setFocus)

    def _actualizar_barra_cajero(self):
        """Refresca el label de la barra de estado con el cajero activo."""
        nombre_str = CajeroActivo.nombre.upper()
        if CajeroActivo.numero == 2:
            from src.updater.github_updater import get_local_version
            self.lbl_version.setText(f"🟢 {nombre_str}  |  CF {get_local_version()}")
            self.lbl_version.setStyleSheet("color: #10b981; font-weight: 900; font-size: 11px; letter-spacing: 1px; border: none;")
            self.btn_candado.setStyleSheet("""
                QPushButton {
                    background: #059669; color: white; border-radius: 5px;
                    font-size: 14px; font-weight: bold; border: 1px solid #10b981;
                }
                QPushButton:hover { background: #EF4444; border-color: #EF4444; }
            """)
        else:
            from src.updater.github_updater import get_local_version
            self.lbl_version.setText(f"🔵 {nombre_str}  |  CF {get_local_version()}")
            self.lbl_version.setStyleSheet("color: #60a5fa; font-weight: 900; font-size: 11px; letter-spacing: 1px; border: none;")
            self.btn_candado.setStyleSheet("""
                QPushButton {
                    background: #1E3A8A; color: white; border-radius: 5px;
                    font-size: 14px; font-weight: bold; border: 1px solid #3B82F6;
                }
                QPushButton:hover { background: #EF4444; border-color: #EF4444; }
            """)




    def _apply_screen_layout(self):
        """Ajusta tamaños al monitor real (14\" laptop vs 24\" POS)."""
        from src.utils.qt_dpi import terminal_layout_metrics

        m = terminal_layout_metrics()
        ls = m["layout_scale"]

        self.main_layout.setContentsMargins(m["main_margin"], m["main_margin"], m["main_margin"], m["main_margin"])

        self.header_frame.setFixedHeight(m["header_height"])
        self.dashboard_frame.setFixedHeight(m["dashboard_height"])
        self.status_bar.setFixedHeight(m["status_height"])
        self._shortcuts_scroll.setFixedHeight(m["shortcuts_height"])
        self._apply_status_bar_controls(m)

        self.txt_scan.setMinimumHeight(m["scan_min_height"])
        scan_px = m["scan_font"]
        total_px = m["total_font"]
        side_px = m["side_font"]
        title_px = m["title_font"]
        row_h = m["table_row"]

        self.lbl_terminal_title.setStyleSheet(
            f"font-size: {title_px}px; font-weight: bold;"
        )
        self.lbl_total_val.setStyleSheet(
            f"font-size: {total_px}px; color: #059669; font-weight: 900; border: none;"
        )
        self.txt_scan.setStyleSheet(f"""
            QLineEdit {{
                background: white; border: 3px solid #3B82F6; border-radius: 12px;
                color: #1E3A8A; font-size: {scan_px}px; padding: 12px; font-weight: 900;
            }}
        """)
        self._style_side_labels(cambio_highlight=False, side_px=side_px)
        self.tabla.verticalHeader().setDefaultSectionSize(row_h)
        self._apply_status_bar_shortcuts_layout(ls)
        self._apply_tabla_column_layout()
        self._layout_list_results_popup(m)

    def _build_side_summary_row(self, parent_layout, title: str):
        """Fila resumen: etiqueta pequeña + valor numérico grande."""
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)
        lbl_t = QLabel(title)
        lbl_v = QLabel("0")
        lbl_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_t.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        lbl_v.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(lbl_t)
        row.addWidget(lbl_v, stretch=1)
        parent_layout.addLayout(row)
        return lbl_t, lbl_v

    def _style_side_labels(self, cambio_highlight=False, side_px=None):
        """Resumen lateral: título discreto + valor numérico en negrita."""
        from src.utils.qt_dpi import terminal_layout_metrics

        if side_px is None:
            side_px = terminal_layout_metrics()["side_font"]
        theme = config.get("theme", "light")
        title_c = "#94A3B8" if theme == "dark" else "#64748B"
        value_c = "#F8FAFC" if theme == "dark" else "#0F172A"
        cambio_c = "#34D399" if theme == "dark" else "#059669"
        title_px = max(12, side_px - 4)
        value_px = max(16, side_px)
        cambio_px = max(17, side_px + 1)
        title_style = (
            f"font-family: 'Segoe UI'; font-size: {title_px}px; color: {title_c}; "
            "font-weight: 600; border: none; background: transparent;"
        )
        value_style = (
            f"font-family: 'Segoe UI'; font-size: {value_px}px; color: {value_c}; "
            "font-weight: 800; border: none; background: transparent;"
        )
        cambio_style = (
            f"font-family: 'Segoe UI'; font-size: {cambio_px}px; color: {cambio_c}; "
            "font-weight: 800; border: none; background: transparent;"
        )
        for lbl_t in (
            self.lbl_side_cant_t, self.lbl_side_total_t, self.lbl_side_ahorro_t,
            self.lbl_side_pagos_t, self.lbl_side_cambio_t,
        ):
            lbl_t.setStyleSheet(title_style)
        for lbl_v in (self.lbl_side_cant, self.lbl_side_total, self.lbl_side_ahorro, self.lbl_side_pagos):
            lbl_v.setStyleSheet(value_style)
        self.lbl_side_cambio.setStyleSheet(cambio_style if cambio_highlight else value_style)

    def _apply_status_bar_controls(self, metrics):
        """Escala altura de botones del pie para que coincidan con status_bar."""
        from src.utils.qt_dpi import scale_px

        ls = metrics["layout_scale"]
        ctrl_h = metrics["status_control_height"]
        icon_sz = metrics["status_icon_size"]

        sl = self.status_bar.layout()
        if sl is not None:
            sl.setContentsMargins(scale_px(15, ls), scale_px(5, ls), scale_px(5, ls), scale_px(5, ls))

        for attr in ("btn_teclado", "btn_theme", "btn_espera"):
            btn = getattr(self, attr, None)
            if btn is not None:
                btn.setFixedHeight(ctrl_h)

        for attr in ("btn_candado", "btn_chatbot"):
            btn = getattr(self, attr, None)
            if btn is not None:
                btn.setFixedSize(icon_sz, icon_sz)

    def _apply_status_bar_shortcuts_layout(self, ls=None):
        """F-keys blancas: todas visibles junto a candado/chatbot."""
        if not hasattr(self, "_shortcuts_scroll") or not self.shortcut_buttons:
            return
        from src.utils.qt_dpi import layout_scale, scale_px, TERMINAL_STATUS_CTRL_H

        if ls is None:
            ls = layout_scale()
        viewport_w = self._shortcuts_scroll.viewport().width()
        if viewport_w < 80:
            return

        n = len(self.shortcut_buttons)
        spacing = self._hints_layout.spacing()

        if viewport_w < 420:
            icon_w = 0
        else:
            icon_w = 0

        gaps = spacing * max(0, n - 1)
        available = max(0, viewport_w - icon_w - gaps)
        min_w = scale_px(34, ls)
        max_w = scale_px(45, ls)
        btn_w = max(min_w, min(max_w, int(available / n) if n else max_w))
        btn_h = scale_px(TERMINAL_STATUS_CTRL_H, ls)
        font_px = 13 if btn_w >= scale_px(40, ls) else 11
        style = self._shortcut_btn_base_style.format(font_px=font_px)
        for btn in self.shortcut_buttons:
            btn.setFixedSize(btn_w, btn_h)
            btn.setStyleSheet(style)

        content_w = icon_w + n * btn_w + gaps
        self._hints_widget.setMinimumWidth(content_w)
        if content_w > viewport_w:
            self._shortcuts_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            bar = self._shortcuts_scroll.horizontalScrollBar()
            QTimer.singleShot(0, lambda: bar.setValue(bar.maximum()))
        else:
            self._shortcuts_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def _apply_tabla_column_layout(self):
        if not hasattr(self, "tabla"):
            return
        vw = self.tabla.viewport().width()
        if vw < 320:
            return
        self.tabla.setColumnWidth(0, max(60, int(vw * 0.08)))
        self.tabla.setColumnWidth(2, max(70, int(vw * 0.15)))
        self.tabla.setColumnWidth(3, max(56, int(vw * 0.10)))
        self.tabla.setColumnWidth(4, max(64, int(vw * 0.10)))
        self.tabla.setColumnWidth(5, max(70, int(vw * 0.15)))

    def _layout_list_results_popup(self, metrics=None):
        if not hasattr(self, "list_results") or not hasattr(self, "dashboard_frame"):
            return
        from src.utils.qt_dpi import terminal_layout_metrics, scale_px
        if metrics is None:
            metrics = terminal_layout_metrics()
        popup_y = self.dashboard_frame.y() - metrics["list_results_h"] - scale_px(8, metrics["layout_scale"])
        self.list_results.setGeometry(
            self.dashboard_frame.x() + 10,
            max(0, popup_y),
            metrics["list_results_w"],
            metrics["list_results_h"],
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_screen_layout()
        if hasattr(self, "list_results"):
            from src.utils.qt_dpi import terminal_layout_metrics
            self._layout_list_results_popup(terminal_layout_metrics())

    def actualizar_reloj(self):
        ahora = datetime.now()
        self.lbl_fecha.setText(f"Fecha:  {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Cada 5 segundos verificamos los niveles de efectivo en caja para activar alertas SOS
        if ahora.second % 5 == 0:
            self.check_alertas_efectivo()
            
        # Cada 3 segundos verificamos si el Administrador ha solicitado un arqueo remoto (Señal de Cierre)
        if ahora.second % 3 == 0:
            self.check_solicitud_cierre_remoto()
        
        # Si es el inicio de un nuevo día (Medianoche exacta), forzamos el cierre automático
        if ahora.hour == 0 and ahora.minute == 0 and ahora.second == 1:
            self.check_midnight_closure()

    def asegurar_foco_escaner(self):
        if self.isVisible() and self.txt_scan:
            # Si el foco está en la tabla o en los resultados de búsqueda, no robarlo (están navegando)
            if self.tabla.hasFocus() or self.list_results.hasFocus():
                return
            # Si hay algún widget modal activo (diálogo de cantidad, cobro, etc.), no robarlo
            from PyQt6.QtWidgets import QApplication
            if QApplication.activeModalWidget() is not None:
                return
            # Si el chatbot flotante está visible y activo, no robar el foco
            if getattr(self, 'chatbot_widget', None) is not None and self.chatbot_widget.isVisible() and self.chatbot_widget.isActiveWindow():
                return
            # Si el escáner no tiene el foco, restaurarlo de inmediato
            if not self.txt_scan.hasFocus():
                self.txt_scan.setFocus()

    def check_alertas_efectivo(self):
        """Monitorea el efectivo en caja y parpadea los bordes si excede los límites."""
        # Evitar parpadeos superpuestos si ya hay un feedback temporal corriendo
        if hasattr(self, '_parpadeo_activo') and self._parpadeo_activo:
            return
        from src.config import config
        c_id = config.get("caja_id", 1)
        efectivo = db_manager.get_efectivo_en_caja(c_id)
        
        # Obtener los umbrales configurados por el administrador (o usar defaults industriales)
        from src.config import config as _c
        umbral_naranja = float(_c.get("limite_efectivo_naranja", 50000.0))
        umbral_rojo    = float(_c.get("limite_efectivo_rojo",    70000.0))
        
        color_borde = None
        if efectivo >= umbral_rojo:
            color_borde = "#F97316"  # NARANJA (Crítico - Retiro Urgente)
        elif efectivo >= umbral_naranja:
            color_borde = "#EAB308"  # AMARILLO (Advertencia - Retiro Próximo)
            
        if color_borde:
            self._parpadeo_activo = True
            estilo_orig = self.dashboard_frame.styleSheet()
            
            # Parpadeo: encender borde grueso
            self.dashboard_frame.setStyleSheet(f"background-color: white; border: 5px solid {color_borde}; border-radius: 8px;")
            
            def apagar():
                self.dashboard_frame.setStyleSheet(estilo_orig)
                self._parpadeo_activo = False
                
            # Apagar el borde en 800ms para crear el efecto intermitente
            QTimer.singleShot(800, apagar)

    def check_midnight_closure(self):
        """ Verifica si hay ventas del día anterior y reinicia la app si es necesario """
        from src.services.caja_service import verificar_y_realizar_autocierre
        from PyQt6.QtWidgets import QMessageBox, QApplication
        
        hizo, monto = verificar_y_realizar_autocierre()
        if hizo:
             QMessageBox.warning(self, "🌙 CIERRE AUTOMÁTICO DIARIO", 
                f"El sistema ha realizado el cierre automático del día anterior por valor de ${monto:.2f}.\n\n"
                "Para continuar, la aplicación se reiniciará para que inicies el nuevo turno del día.")
             QApplication.exit(888) # Código de reinicio en main.py

    def check_solicitud_cierre_remoto(self):
        if not self.isVisible():
            return
            
        if getattr(self, '_cierre_en_progreso', False):
            return
 
        try:
            from src.config import config
            c_id = config.get("caja_id", 1)
            
            # 1. Obtener la fecha del último inicio de turno (APERTURA) de esta caja
            res_ap = db_manager.execute_query(
                "SELECT fecha FROM movimientos_caja WHERE tipo = 'APERTURA' AND caja_id = ? ORDER BY id DESC LIMIT 1",
                (c_id,)
            )
            ult_apertura = "1970-01-01 00:00:00"
            if res_ap:
                ult_apertura = res_ap[0]['fecha']
                
            # 2. Consultar si el supervisor ha enviado una SOLICITUD_CIERRE creada DURANTE este turno
            res = db_manager.execute_query(
                "SELECT id, observaciones FROM movimientos_caja WHERE tipo = 'SOLICITUD_CIERRE' AND caja_id = ? AND observaciones NOT LIKE '%%PROCESADO%%' AND fecha >= ? ORDER BY id DESC LIMIT 1",
                (c_id, ult_apertura)
            )
            if res:
                self._cierre_en_progreso = True
                
                # Marcar todas las solicitudes pendientes de este turno como PROCESADO para que no se vuelvan a gatillar
                db_manager.execute_non_query(
                    "UPDATE movimientos_caja SET observaciones = 'PROCESADO' WHERE tipo = 'SOLICITUD_CIERRE' AND caja_id = ? AND fecha >= ?",
                    (c_id, ult_apertura)
                )
                
                # Mostrar cuadro de diálogo informativo industrial alertando del Cierre Remoto
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "⚠️ ARQUEO DE CAJA REQUERIDO",
                    "La administración central ha solicitado el arqueo y cierre de esta terminal.\n\n"
                    "Por favor, proceda a ingresar el efectivo contado físico para finalizar la sesión.",
                    QMessageBox.Ok
                )
                
                # Gatillar la ventana de cierre (Paso 7)
                self.abrir_cierre_caja()
                self._cierre_en_progreso = False
        except Exception as e:
            self._cierre_en_progreso = False
            print(f"Error verificando cierre remoto: {e}")

    def actualizar_busqueda(self):
        # En lugar de buscar en cada tecla, esperamos 250ms.
        # Si entra otra tecla (como hace un escáner), el timer se reinicia.
        self.search_timer.start(250)
        
    def _do_busqueda(self):
        txt = self.txt_scan.text().strip()
        if not txt or txt.startswith('+'):
            self.list_results.hide()
            return
            
        # Ignorar la parte del multiplicador en la búsqueda visual para que no falle
        if '*' in txt:
            partes = txt.split('*', 1)
            txt = partes[1].strip()
            if not txt:
                self.list_results.hide()
                return
                
        res = db_manager.execute_query("SELECT id, nombre, precio, stock, cant_oferta, precio_oferta FROM productos WHERE id = ? OR nombre LIKE ? LIMIT 5", (txt, f"%{txt}%"))
        self.list_results.clear()
        
        if res:
            for r in res:
                stk = float(r['stock'] or 0.0)
                stk_str = f"{int(stk)}" if stk.is_integer() else f"{stk:.2f}"
                item = QListWidgetItem(f"📦 Stock: {stk_str}  |  {r['id']} - {r['nombre']} - ${r['precio']:.2f}")
                item.setData(Qt.UserRole, r)
                self.list_results.addItem(item)
            self.list_results.setCurrentRow(0)
            self.list_results.show()
            self.list_results.raise_()
        else:
            item = QListWidgetItem(f"🚫 No hay resultados para '{txt}'")
            item.setData(Qt.UserRole, None)
            item.setForeground(QColor("#FF0000"))
            self.list_results.addItem(item)
            self.list_results.clearSelection()
            self.list_results.show()
            self.list_results.raise_()

    def seleccionar_item_busqueda(self):
        current = self.list_results.currentItem()
        if current:
            p = current.data(Qt.UserRole)
            if p:
                # Si el usuario había ingresado un multiplicador en el texto, lo rescatamos
                txt_raw = self.txt_scan.text().strip()
                cant_multi = 1.0
                if '*' in txt_raw:
                    try: cant_multi = float(txt_raw.split('*')[0].replace(',', '.'))
                    except: pass
                self.agregar_a_tabla(p, cant_multi)
                self.txt_scan.clear()
                self.list_results.hide()
                self.txt_scan.setFocus()

    def procesar_scan(self):
        from src.utils.barcode_parser import BarcodeParser
        txt_raw = self.txt_scan.text()
        
        txt, cantidad_multiplicador = BarcodeParser.parse_scan_text(txt_raw)
        
        if not txt: 
            self.finalizar_venta()
            return

        # Lógica PRO: Artículo Común intencional usando el prefijo '+'
        p_manual, success = BarcodeParser.try_parse_manual_item(txt_raw.strip())
        if success:
            self.agregar_a_tabla(p_manual, cantidad_multiplicador)
            self.txt_scan.clear()
            self.list_results.hide()
            self.txt_scan.setFocus()
            return
        
        # Si hay lista de búsqueda abierta
        if not self.list_results.isHidden():
            current = self.list_results.currentItem()
            if current:
                p = current.data(Qt.UserRole)
                if p:
                    self.agregar_a_tabla(p, cantidad_multiplicador)
                    self.txt_scan.clear()
                    self.list_results.hide()
                    self.txt_scan.setFocus()
                    return

        # --- BUSQUEDA DE PRODUCTO ---
        # 1. Intentar búsqueda por ID exacto (Barcode completo) primero
        res_direct = db_manager.execute_query("SELECT id, nombre, precio, stock, cant_oferta, precio_oferta FROM productos WHERE id = ?", (txt,))
        if res_direct:
            p = res_direct[0]
            self.agregar_a_tabla(p, cantidad_multiplicador)
            self.txt_scan.clear()
            self.list_results.hide()
            self.txt_scan.setFocus()
            return

        # 2. Lógica PRO: Códigos de Balanza (Configuración Dinámica)
        if BarcodeParser.is_balanza_ean(txt):
            from src.repositories.producto_repository import ProductoRepository
            plu, plu_limpio = BarcodeParser.extract_plu_from_barcode(txt)
            p = ProductoRepository.obtener_por_plu_balanza(plu)
            if p:
                precio_unitario = float(p['precio'])
                _, cantidad_balanza = BarcodeParser.parse_balanza_code(txt, precio_unitario)
                if cantidad_balanza is not None and cantidad_balanza > 0:
                    self.agregar_a_tabla(p, cantidad_balanza)
                    self.txt_scan.clear()
                    self.list_results.hide()
                    self.txt_scan.setFocus()
                    return
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "Balanza: Producto no encontrado",
                    f"Etiqueta de balanza leída (PLU {plu_limpio}), pero no hay producto con ese código en inventario.\n\n"
                    f"El ID del producto debe coincidir con el PLU de la balanza (ej. producto 2050 → PLU 02050).\n"
                    f"Código escaneado: {txt}"
                )
                self.txt_scan.selectAll()
                self.txt_scan.setFocus()
                return

        # 3. Escaneo directo o búsqueda por nombre (Productos Normales)
        res = db_manager.execute_query("SELECT id, nombre, precio, stock, cant_oferta, precio_oferta FROM productos WHERE id = ? OR nombre LIKE ?", (txt, f"%{txt}%"))

        if res:
            p = res[0]
            self.agregar_a_tabla(p, cantidad_multiplicador)
            self.txt_scan.clear()
            self.list_results.hide()
            self.txt_scan.setFocus()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Encontrado", f"No se encontró ningún producto con el código o nombre: '{txt}'")
            self.txt_scan.selectAll()
            self.txt_scan.setFocus()

    def agregar_a_tabla(self, p, cantidad=1.0):
        # OPTIMIZACION: Congelar el renderizado de la tabla hasta que terminen todos los calculos
        self.setUpdatesEnabled(False)
        self.en_venta = True
        p_id = str(p['id'])
        precio_base = float(p['precio'])
        
        cant_of = 0.0
        precio_of = 0.0
        if hasattr(p, 'keys'):
            if 'cant_oferta' in p.keys(): cant_of = float(p['cant_oferta'] or 0.0)
            if 'precio_oferta' in p.keys(): precio_of = float(p['precio_oferta'] or 0.0)
        
        # 1. Agrupar si el producto ya existe en la tabla (Auto-Suma), excepto Artículos Comunes
        if p_id != "000":
            for i in range(self.tabla.rowCount()):
                if self.tabla.item(i, 0).text() == p_id:
                    old_cant = float(self.tabla.item(i, 3).text())
                    new_cant = old_cant + cantidad
                    if not self._validar_stock(p, p_id, new_cant):
                        self.setUpdatesEnabled(True)
                        return
                    
                    # Verificamos si alcanza o supera la cantidad de oferta
                    if cant_of > 0 and precio_of > 0 and new_cant >= cant_of:
                        p_aplicar = precio_of
                        desc_total = (precio_base - precio_of) * new_cant
                        display_name = f"🔥 [OFERTA] {p['nombre']}"
                    else:
                        p_aplicar = precio_base
                        desc_total = 0.0
                        display_name = str(p['nombre'])
                        
                    # Actualizar Nombre con el distintivo
                    self.tabla.item(i, 1).setText(display_name)
                    # Actualizar Precio Unitario Aplicado
                    self.tabla.item(i, 2).setText(fmt_moneda_sin_centavos(p_aplicar))
                    # Actualizar cantidad
                    self.tabla.item(i, 3).setText(f"{new_cant:.2f}" if new_cant % 1 != 0 else f"{int(new_cant)}")
                    # Actualizar Descuento Total
                    self.tabla.item(i, 4).setText(fmt_moneda_sin_centavos(desc_total))
                    # Actualizar Subtotal
                    self.tabla.item(i, 5).setText(fmt_moneda_sin_centavos(new_cant * p_aplicar))
                    self.last_active_row = i
                    self._reaplicar_estilo_fila(i)
                    
                    # Foco visual sutil centrado en el duplicado
                    self.tabla.selectRow(i)
                    self.actualizar_totales()
                    self.setUpdatesEnabled(True)
                    self.repaint()
                    return

        if not self._validar_stock(p, p_id, cantidad):
            self.setUpdatesEnabled(True)
            return

        # 2. Si no existe, calculamos para la inserción de la fila nueva
        if cant_of > 0 and precio_of > 0 and cantidad >= cant_of:
            p_aplicar = precio_of
            desc_total = (precio_base - precio_of) * cantidad
            display_name = f"🔥 [OFERTA] {p['nombre']}"
        else:
            p_aplicar = precio_base
            desc_total = 0.0
            display_name = str(p['nombre'])

        row = self.tabla.rowCount()
        self.tabla.insertRow(row)
        
        items = [p_id, display_name, fmt_moneda_sin_centavos(p_aplicar), f"{cantidad:.2f}" if cantidad % 1 != 0 else f"{int(cantidad)}", fmt_moneda_sin_centavos(desc_total), fmt_moneda_sin_centavos(p_aplicar * cantidad)]
        for idx, v in enumerate(items):
            it = QTableWidgetItem(v)
            it.setTextAlignment(Qt.AlignCenter)
            
            font = it.font()
            font.setBold(True) # Inquebrantable para toda la fila
            it.setFont(font)
            
            if idx == 1:
                it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            elif idx in (2, 3, 4, 5):
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            if idx == 5: 
                it.setForeground(QColor("#059669")) # Esmeralda fuerte
                it.setFlags(it.flags() & ~Qt.ItemIsSelectable) # Deshabilitar selección para blindar su fondo verde agua
            
            self.tabla.setItem(row, idx, it)

        self.last_active_row = row
        self._reaplicar_estilo_fila(row)
        self.tabla.selectRow(row)
        self.actualizar_totales()
        
        # Sonido BEEP de Escáner ultra rápido
        if AUDIO_ENABLED:
            def fast_beep():
                try: import winsound; winsound.Beep(2500, 50)
                except: pass
            threading.Thread(target=fast_beep, daemon=True).start()
            
        # OPTIMIZACION: Liberar la pantalla para que dibuje el resultado final en 1 solo cuadro
        self.setUpdatesEnabled(True)
        self.repaint()

    def actualizar_totales(self):
        # Refrescar en cascada los estilos para que el destaque azul y el subtotal verde agua se muevan dinámicamente
        for i in range(self.tabla.rowCount()):
            self._reaplicar_estilo_fila(i)
            
        total = sum(parse_float_safe(self.tabla.item(i, 5).text()) for i in range(self.tabla.rowCount()))
        cant = sum(float(self.tabla.item(i, 3).text()) for i in range(self.tabla.rowCount()))
        total_desc = sum(parse_float_safe(self.tabla.item(i, 4).text()) for i in range(self.tabla.rowCount()))
        
        # El total grande vuelve a usar el formato sin centavos con comas de miles
        total_str = fmt_moneda_sin_centavos(total)
        self.lbl_total_val.setText(total_str)
        self.lbl_cant_val.setText(f"{int(cant)}")
        
        # Si estamos agregando items, limpiamos los "Pagos" y "Cambio" de la venta anterior
        if self.en_venta:
            cant_txt = f"{cant:.2f}" if cant % 1 != 0 else f"{int(cant):,}"
            self.lbl_side_cant.setText(cant_txt)
            total_sin = fmt_moneda_sin_centavos(total)
            desc_sin = fmt_moneda_sin_centavos(total_desc)
            self.lbl_side_total.setText(total_sin)
            if total_desc > 0:
                self.lbl_side_ahorro.setText(desc_sin)
                self.lbl_side_ahorro_t.show()
                self.lbl_side_ahorro.show()
            else:
                self.lbl_side_ahorro_t.hide()
                self.lbl_side_ahorro.hide()
            self.lbl_side_pagos.setText("0")
            self.lbl_side_cambio.setText("0")
            self._style_side_labels(cambio_highlight=False)
            
        # Gatillar la animación interactiva de ahorro total
        self.animar_ahorro(total_desc)

    def animar_ahorro(self, nuevo_ahorro):
        """ 
        Animación interactiva premium tipo 'saldo ascendente' (+100).
        Incrementa el valor del ahorro de forma asíncrona y fluida.
        """
        if not hasattr(self, 'current_ahorro'):
            self.current_ahorro = 0.0
            
        # Detener respiración si el ahorro es 0 o está cambiando
        if hasattr(self, '_respiracion_anim') and self._respiracion_anim:
            self._respiracion_anim.stop()
            self._respiracion_anim = None
            
        if nuevo_ahorro <= 0:
            self.current_ahorro = 0.0
            self.lbl_ahorro_val.hide()
            return
            
        self.lbl_ahorro_val.show()
        
        # Color y tamaño de impacto (Naranja vibrante para el incremento)
        self.lbl_ahorro_val.setStyleSheet("font-size: 48px; color: #FF4500; font-weight: 900; border: none;")
        
        from src.utils.qt_compat import VariantFloatAnimation
        if hasattr(self, '_ahorro_anim') and self._ahorro_anim:
            self._ahorro_anim.stop()
            
        self._ahorro_anim = VariantFloatAnimation(self)
        self._ahorro_anim.setStartValue(self.current_ahorro)
        self._ahorro_anim.setEndValue(nuevo_ahorro)
        self._ahorro_anim.setDuration(2000) # 2000ms (2.0s) de animación suave e impactante
        
        def on_value_changed(value):
            self.lbl_ahorro_val.setText(f"🎉 +${value:,.2f}")
            
        def on_finished():
            self.current_ahorro = nuevo_ahorro
            self.lbl_ahorro_val.setText(f"🎉 AHORRAS: ${nuevo_ahorro:,.2f}")
            # Al terminar el conteo, iniciar el bucle continuo de respiración (zoom + glow flash)
            self.iniciar_respiracion_ahorro()
            
        self._ahorro_anim.valueChanged.connect(on_value_changed)
        self._ahorro_anim.finished.connect(on_finished)
        self._ahorro_anim.start()

    def iniciar_respiracion_ahorro(self):
        """
        Inicia un efecto continuo de respiración (zoom + brillo intermitente) 
        en la etiqueta de ahorro para que se vea súper llamativa y orgánica.
        """
        from src.utils.qt_compat import VariantFloatAnimation, easing_sine_curve
        
        if hasattr(self, '_respiracion_anim') and self._respiracion_anim:
            return
            
        self._respiracion_anim = VariantFloatAnimation(self)
        self._respiracion_anim.setStartValue(0.0)
        self._respiracion_anim.setEndValue(1.0)
        self._respiracion_anim.setDuration(1500) # Ciclo suave de 1.5 segundos
        self._respiracion_anim.setEasingCurve(easing_sine_curve())
        self._respiracion_anim.setLoopCount(-1) # Bucle infinito
        
        def on_step(t):
            # Normalizar el valor del seno (-1.0 a 1.0) a un rango limpio de 0.0 a 1.0
            val_norm = (t + 1.0) / 2.0
            
            # 1. Efecto Zoom: Oscila suavemente entre 36px y 46px
            size = int(36 + (10 * val_norm))
            
            # 2. Efecto Brillo (Glow Flash): El radio va de 10 a 30 y la opacidad de 80 a 230
            glow_radius = int(10 + (20 * val_norm))
            alpha = int(80 + (150 * val_norm))
            
            # Aplicar estilos con naranja vibrante premium (#FF4500)
            self.lbl_ahorro_val.setStyleSheet(f"font-size: {size}px; color: #FF4500; font-weight: 900; border: none;")
            
            if hasattr(self, 'ahorro_glow') and self.ahorro_glow:
                self.ahorro_glow.setBlurRadius(glow_radius)
                self.ahorro_glow.setColor(QColor(255, 69, 0, alpha))
                
        self._respiracion_anim.valueChanged.connect(on_step)
        self._respiracion_anim.start()

    def abrir_retiro_efectivo(self):
        """Abre el panel rápido de retiro de efectivo de caja (F5)."""
        from src.config import config
        c_id = config.get("caja_id", 1)
        efectivo = db_manager.get_efectivo_en_caja(c_id)
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.setGraphicsEffect(blur)
        
        dlg = DialogoRetiroEfectivo(efectivo, parent=self)
        if qt_exec(dlg) and dlg.monto_retirado > 0:
            # Solicitar PIN de confirmación del operador activo
            pin_dlg = DialogoPIN(CajeroActivo.nombre, parent=self)
            if qt_exec(pin_dlg) and pin_dlg.ok:
                monto = dlg.monto_retirado
                motivo = getattr(dlg, "motivo", "Retiro rápido de efectivo en terminal")
                usuario = CajeroActivo.nombre
                from src.config import config
                c_id = config.get("caja_id", 1)
                query = "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id) VALUES ('RETIRO', ?, ?, ?, ?)"
                if db_manager.execute_non_query(query, (monto, usuario, motivo, c_id)):
                    self.flash_feedback(success=True)
                    # Marcar apertura como autorizada para el monitor de seguridad
                    self._apertura_autorizada = True
                    # Abrir cajón físicamente
                    printer_manager.abrir_cajon()
                    # Imprimir ticket de comprobante físico
                    printer_manager.imprimir_movimiento_caja('RETIRO DE EFECTIVO', monto, motivo, usuario, c_id)
                    self.monitor_cajon_bloqueante(manual=True)
                    self.check_alertas_efectivo()
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", "No se pudo registrar el retiro en la base de datos.")
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)

    def abrir_ingreso_efectivo(self):
        """Abre el panel de ingreso manual de dinero a la caja (F6)."""
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.setGraphicsEffect(blur)
        
        dlg = DialogoIngresoEfectivo(parent=self)
        if qt_exec(dlg) and dlg.monto_ingresado > 0:
            # Solicitar PIN de confirmación del operador activo
            pin_dlg = DialogoPIN(CajeroActivo.nombre, parent=self)
            if qt_exec(pin_dlg) and pin_dlg.ok:
                monto = dlg.monto_ingresado
                motivo = getattr(dlg, "motivo", "Ingreso manual de efectivo en terminal")
                usuario = CajeroActivo.nombre
                from src.config import config
                c_id = config.get("caja_id", 1)
                
                # Novedad: Si es un abono a Fiado, procesar la deuda en DB
                if getattr(dlg, "tipo_ingreso", "") == "FIADO" and getattr(dlg, "cliente_id", None):
                    nuevo_saldo = dlg.deuda_actual - monto
                    db_manager.execute_non_query("UPDATE clientes SET deuda_actual = ? WHERE id = ?", (nuevo_saldo, dlg.cliente_id))
                    db_manager.execute_non_query(
                        "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) VALUES (?, ?, ?, ?, ?)",
                        (dlg.cliente_id, 'ABONO', monto, nuevo_saldo, 'Abono Fiado en Caja')
                    )

                query = "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id) VALUES ('INGRESO', ?, ?, ?, ?)"
                if db_manager.execute_non_query(query, (monto, usuario, motivo, c_id)):
                    self.flash_feedback(success=True)
                    # Abrir cajón físicamente
                    printer_manager.abrir_cajon()
                    # Imprimir ticket de comprobante físico
                    printer_manager.imprimir_movimiento_caja('INGRESO DE EFECTIVO', monto, motivo, usuario, c_id)
                    self.monitor_cajon_bloqueante(manual=True)
                    self.check_alertas_efectivo()
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso en la base de datos.")
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)

    def showEvent(self, event):
        super().showEvent(event)
        from src.config import config as _c
        _c._load_config()
        self._refresh_urgencia_stock_banner()

    def keyPressEvent(self, event):
        k = event.key()
        
        # F1: Foco al buscador
        if k == Qt.Key_F1:
            self.txt_scan.setFocus(); self.txt_scan.selectAll()
            return
            
        # F3: Historial
        if k == Qt.Key_F3:
            self.abrir_historial_dia()
            return

        # F12: Cobrar
        if k == Qt.Key_F12:
            self.finalizar_venta()
            return

        # F5: Retiro
        if k == Qt.Key_F5:
            self.abrir_retiro_efectivo()
            return

        # F6: Ingreso
        if k == Qt.Key_F6:
            self.abrir_ingreso_efectivo()
            return

        # F8: Bloquear
        if k == Qt.Key_F8:
            self.bloquear_terminal()
            return

        # F4: Cierre de Caja
        if k == Qt.Key_F4:
            self.abrir_cierre_caja()
            return

        # Flecha Abajo desde el buscador
        if self.txt_scan.hasFocus() and k == Qt.Key_Down:
            if not self.list_results.isHidden():
                self.list_results.setFocus()
            elif self.tabla.rowCount() > 0:
                self.tabla.setFocus()
                self.tabla.selectRow(self.tabla.rowCount() - 1)
                self.tabla.setCurrentCell(self.tabla.rowCount() - 1, 3)
                QTimer.singleShot(0, self._on_tabla_nav_row_only)
            return

        # Navegar en lista de resultados
        if self.list_results.hasFocus():
            if k == Qt.Key_Up and self.list_results.currentRow() == 0:
                self.txt_scan.setFocus()
                return
            if k in [Qt.Key_Return, Qt.Key_Enter]:
                self.seleccionar_item_busqueda()
                return

        # Edición en la tabla
        if self.tabla.hasFocus():
            row = self.tabla.currentRow()
            if row != -1:
                if k in [Qt.Key_Left, Qt.Key_Right]:
                    old_v = float(self.tabla.item(row, 3).text())
                    inc = 1 if k == Qt.Key_Right else -1
                    new_v = max(0, old_v + inc)
                    
                    if new_v <= 0:
                        self.tabla.removeRow(row)
                        self.actualizar_totales()
                        self.txt_scan.setFocus()
                        return
                        
                    # 1. "Se infla para que el cliente lo vea"
                    self.tabla.setRowHeight(row, 70)
                    
                    it_edit = self.tabla.item(row, 3)
                    it_edit.setText(f"{new_v:.2f}" if new_v % 1 != 0 else f"{int(new_v)}")
                    font_inflada = it_edit.font()
                    font_inflada.setPointSize(32)
                    font_inflada.setBold(True)
                    it_edit.setFont(font_inflada)
                    it_edit.setForeground(QColor("#FF0000")) # Rojo advertencia
                    
                    # Verificación dinámica de ofertas al ajustar cantidad
                    p_id = self.tabla.item(row, 0).text()
                    res_of = db_manager.execute_query("SELECT precio, cant_oferta, precio_oferta FROM productos WHERE id=?", (p_id,))
                    if res_of and p_id != "000":
                        p_base = float(res_of[0]['precio'])
                        c_of = float(res_of[0]['cant_oferta'] or 0.0)
                        p_of = float(res_of[0]['precio_oferta'] or 0.0)
                        
                        if c_of > 0 and p_of > 0 and new_v >= c_of:
                            p_ap = p_of
                            desc_t = (p_base - p_of) * new_v
                            nombre_txt = self.tabla.item(row, 1).text()
                            if "🔥 [OFERTA]" not in nombre_txt:
                                self.tabla.item(row, 1).setText(f"🔥 [OFERTA] {nombre_txt}")
                        else:
                            p_ap = p_base
                            desc_t = 0.0
                            nombre_txt = self.tabla.item(row, 1).text()
                            if "🔥 [OFERTA]" in nombre_txt:
                                clean_name = nombre_txt.replace("🔥 [OFERTA] ", "")
                                self.tabla.item(row, 1).setText(clean_name)
                                
                        self.tabla.item(row, 2).setText(fmt_moneda_sin_centavos(p_ap))
                        self.tabla.item(row, 4).setText(fmt_moneda_sin_centavos(desc_t))
                        p_unit = p_ap
                    else:
                        p_unit = parse_float_safe(self.tabla.item(row, 2).text())
                    
                    # Actualizar subtotal
                    it_sub = self.tabla.item(row, 5)
                    it_sub.setText(fmt_moneda_sin_centavos(new_v * p_unit))
                    
                    font_normal = it_sub.font()
                    font_normal.setPointSize(18)
                    it_sub.setFont(font_normal)
                    it_sub.setForeground(QColor("#FF0000"))
                    
                    self._reaplicar_estilo_fila(row)
                    self.actualizar_totales()
                    return # intercepted
                    
                elif event.key() == Qt.Key_Delete:
                    dlg = DialogoAtencion(self)
                    if qt_exec(dlg):
                        self.tabla.removeRow(row)
                        self.actualizar_totales()
                    QTimer.singleShot(50, self.txt_scan.setFocus)
                    return
                    
                elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    nombre = self.tabla.item(row, 1).text()
                    cant_actual = float(self.tabla.item(row, 3).text())
                    
                    dlg = DialogoEditarCantidad(cant_actual, nombre, self)
                    if qt_exec(dlg):
                        new_cant = dlg.get_value()
                        self.tabla.item(row, 3).setText(f"{new_cant:.2f}" if new_cant % 1 != 0 else f"{int(new_cant)}")
                        
                        # Verificación dinámica de ofertas al ingresar con el Enter
                        p_id = self.tabla.item(row, 0).text()
                        res_of = db_manager.execute_query("SELECT precio, cant_oferta, precio_oferta FROM productos WHERE id=?", (p_id,))
                        if res_of and p_id != "000":
                            p_base = float(res_of[0]['precio'])
                            c_of = float(res_of[0]['cant_oferta'] or 0.0)
                            p_of = float(res_of[0]['precio_oferta'] or 0.0)
                            
                            if c_of > 0 and p_of > 0 and new_cant >= c_of:
                                p_ap = p_of
                                desc_t = (p_base - p_of) * new_cant
                                nombre_txt = self.tabla.item(row, 1).text()
                                if "🔥 [OFERTA]" not in nombre_txt:
                                    self.tabla.item(row, 1).setText(f"🔥 [OFERTA] {nombre_txt}")
                            else:
                                p_ap = p_base
                                desc_t = 0.0
                                nombre_txt = self.tabla.item(row, 1).text()
                                if "🔥 [OFERTA]" in nombre_txt:
                                    clean_name = nombre_txt.replace("🔥 [OFERTA] ", "")
                                    self.tabla.item(row, 1).setText(clean_name)
                                    
                            self.tabla.item(row, 2).setText(fmt_moneda_sin_centavos(p_ap))
                            self.tabla.item(row, 4).setText(fmt_moneda_sin_centavos(desc_t))
                            p_unit = p_ap
                        else:
                            p_unit = parse_float_safe(self.tabla.item(row, 2).text())
                        
                        # Actualizar Subtotal
                        self.tabla.item(row, 5).setText(fmt_moneda_sin_centavos(new_cant * p_unit))
                        self._reaplicar_estilo_fila(row)
                        self.actualizar_totales()
                    
                    self.tabla.setRowHeight(row, 40) # Volver al tamaño normal suave
                    QTimer.singleShot(50, self.txt_scan.setFocus)
                    return
                    
            # Permitir que las flechas naveguen por las casillas de la tabla de forma fluida
            if k in (Qt.Key_Up, Qt.Key_Down):
                super().keyPressEvent(event)
                QTimer.singleShot(0, self._on_tabla_nav_row_only)
                return
            super().keyPressEvent(event)
            return

        super().keyPressEvent(event)

    def finalizar_venta(self):
        # Evitar doble apertura accidental
        if hasattr(self, '_cobro_abierto') and self._cobro_abierto: return
        
        try: 
            # Como ahora el total visual no tiene decimales ni comas de miles (son puntos),
            # lo calculamos directamente de la tabla para no perder precisión
            total = sum(parse_float_safe(self.tabla.item(i, 5).text()) for i in range(self.tabla.rowCount()))
        except: return
        if total <= 0: return
        
        self._cobro_abierto = True
        items = []
        for i in range(self.tabla.rowCount()):
            items.append({
                "id": self.tabla.item(i, 0).text(),
                "nombre": self.tabla.item(i, 1).text(),
                "precio": parse_float_safe(self.tabla.item(i, 2).text()),
                "cant": float(self.tabla.item(i, 3).text().replace(",", ".")),
                "subtotal": parse_float_safe(self.tabla.item(i, 5).text())
            })
            
        # --- EFECTO DE DESENFOQUE CINEMÁTICO ---
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)
        
        from src.cajero.paso6_cobro import Paso6Cobro
        dlg = Paso6Cobro(total, items, self)
        dlg.descuentaso_oferta = sum(parse_float_safe(self.tabla.item(i, 4).text()) for i in range(self.tabla.rowCount()))
        
        # Ejecutamos el cobro
        ok = qt_exec(dlg)
        self._cobro_abierto = False
        
        # Quitamos el desenfoque
        self.setGraphicsEffect(None)
        
        if ok:
            # Capturar info de la venta exitosa antes de limpiar
            res = getattr(dlg, 'resultado_venta', None)
            
            self.tabla.setRowCount(0)
            self.en_venta = False
            self.actualizar_totales()
            self.flash_feedback(success=True)
            
            if res:
                self.lbl_side_total.setText(fmt_moneda_sin_centavos(res['total']))
                self.lbl_side_pagos.setText(fmt_moneda_sin_centavos(res['pago_con']))
                self.lbl_side_cambio.setText(fmt_moneda_sin_centavos(res['cambio']))
                self._style_side_labels(cambio_highlight=True)
        else:
            self.flash_feedback(success=False)
            
        QTimer.singleShot(100, self.txt_scan.setFocus)

    def _get_ticket_actual_dict(self):
        import datetime
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        filas = []
        for i in range(self.tabla.rowCount()):
            pid = self.tabla.item(i, 0).text()
            nom = self.tabla.item(i, 1).text()
            pre = self.tabla.item(i, 2).text()
            can = self.tabla.item(i, 3).text()
            des = self.tabla.item(i, 4).text()
            tot = self.tabla.item(i, 5).text()
            filas.append((pid, nom, pre, can, des, tot))

        return {
            "hora": hora,
            "cliente_id": getattr(self, "cliente_id", None),
            "cliente_nombre": getattr(self, "cliente_nombre", "Consumidor Final"),
            "desc_general": getattr(self, "descuento_general", 0.0),
            "total": self.lbl_total_val.text() if hasattr(self, "lbl_total_val") else "0",
            "filas": filas,
        }

    def _restaurar_ticket_dict(self, t):
        self.cliente_id = t.get("cliente_id")
        self.cliente_nombre = t.get("cliente_nombre", "Consumidor Final")
        self.descuento_general = float(t.get("desc_general", 0.0))

        for f in t.get("filas", []):
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            for col, val in enumerate(f):
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignCenter)
                font = it.font()
                font.setBold(True)
                it.setFont(font)
                if col == 1:
                    it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                elif col in (2, 3, 4, 5):
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 5:
                    it.setForeground(QColor("#059669"))
                    it.setFlags(it.flags() & ~Qt.ItemIsSelectable)
                self.tabla.setItem(row, col, it)
            self.last_active_row = row
            self._reaplicar_estilo_fila(row)

        if self.tabla.rowCount() > 0:
            self.en_venta = True
        self.actualizar_totales()

    def _limpiar_para_nuevo_ticket(self):
        self.tabla.setRowCount(0)
        self.en_venta = False
        self._volcar_carrito_a_carteleria(limpiar=True)
        self.cliente_id = None
        self.cliente_nombre = "Consumidor Final"
        self.descuento_general = 0.0
        self.actualizar_totales()

    def _volcar_carrito_a_carteleria(self, limpiar=False):
        from src.services.carteleria_service import CarteleriaService

        if limpiar:
            CarteleriaService.limpiar_carteleria()
            return

        carrito = []
        total_ahorro = 0.0
        ultimo_producto = ""

        for i in range(self.tabla.rowCount()):
            try:
                nombre = self.tabla.item(i, 1).text().replace("🔥 [OFERTA] ", "").replace("🌟 ", "")
                precio_str = self.tabla.item(i, 2).text().replace("$", "")
                precio_str = precio_str.replace(".", "").replace(",", ".")
                precio = float(precio_str)
                carrito.append({"producto": nombre, "precio": precio})
                ultimo_producto = nombre
                try:
                    desc_str = self.tabla.item(i, 4).text().replace("$", "")
                    desc_str = desc_str.replace(".", "").replace(",", ".")
                    total_ahorro += float(desc_str) if desc_str else 0.0
                except Exception:
                    pass
            except Exception:
                pass

        CarteleriaService.notificar_escaneo(carrito, total_ahorro, ultimo_producto)

    def _actualizar_boton_espera(self):
        c = len(self.tickets_espera)
        if c > 0:
            self.btn_espera.setText(f"🔄 {c} Ticket en Espera")
            self.btn_espera.setStyleSheet("""
                QPushButton {
                    background: #EAB308; color: #FFFFFF; border-radius: 5px;
                    font-size: 13px; font-weight: 900; border: 1px solid #CA8A04;
                    padding: 0px 15px;
                }
                QPushButton:hover { background: #CA8A04; }
            """)
        else:
            self.btn_espera.setText("⏳ 0 Espera")
            self.btn_espera.setStyleSheet("""
                QPushButton {
                    background: #FFFFFF; color: #000000; border-radius: 5px;
                    font-size: 13px; font-weight: 900; border: 1px solid #CBD5E1;
                    padding: 0px 15px;
                }
                QPushButton:hover { background: #F1F5F9; }
            """)

    def _swap_ticket_espera(self, *args, **kwargs):
        actual_lleno = self.tabla.rowCount() > 0
        hay_espera = len(self.tickets_espera) > 0

        if not actual_lleno and not hay_espera:
            return

        if actual_lleno and not hay_espera:
            self.tickets_espera.append(self._get_ticket_actual_dict())
            self._limpiar_para_nuevo_ticket()
            self._actualizar_boton_espera()
            self._volcar_carrito_a_carteleria(limpiar=True)
        elif not actual_lleno and hay_espera:
            t = self.tickets_espera.pop(0)
            self._restaurar_ticket_dict(t)
            self._actualizar_boton_espera()
            self._volcar_carrito_a_carteleria()
        elif actual_lleno and hay_espera:
            ticket_a_guardar = self._get_ticket_actual_dict()
            ticket_a_restaurar = self.tickets_espera.pop(0)
            self._limpiar_para_nuevo_ticket()
            self._restaurar_ticket_dict(ticket_a_restaurar)
            self.tickets_espera.append(ticket_a_guardar)
            self._actualizar_boton_espera()
            self._volcar_carrito_a_carteleria()

    def _alerta_tickets_espera(self):
        if self.tickets_espera:
            if AUDIO_ENABLED:
                winsound.Beep(1000, 300)
                winsound.Beep(1000, 300)

    def _hay_ticket_activo(self):
        """True si hay venta pendiente: carrito, cobro abierto o tickets en espera."""
        if getattr(self, "_cobro_abierto", False):
            return True
        if getattr(self, "tabla", None) is not None and self.tabla.rowCount() > 0:
            return True
        if getattr(self, "tickets_espera", None) and len(self.tickets_espera) > 0:
            return True
        return False

    def abrir_cierre_caja(self):
        if self._hay_ticket_activo():
            QMessageBox.warning(
                self,
                "Ticket activo",
                "No podés cerrar turno con productos en el ticket.\n\n"
                "Cobrá la venta (F12) o vaciá el carrito antes de usar F4.",
            )
            QTimer.singleShot(50, self.txt_scan.setFocus)
            return

        # --- EFECTO DE DESENFOQUE CINEMÁTICO ---
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)

        cierre = Paso7CierreCaja(self)
        ok = qt_exec(cierre)
        
        # Quitamos el desenfoque
        self.setGraphicsEffect(None)

        if ok:
            from PyQt6.QtWidgets import QApplication
            from src.config import config
            config.current_user = None
            QApplication.processEvents()
            QApplication.exit(888)
        else:
            QTimer.singleShot(50, self.txt_scan.setFocus)

    def abrir_historial_dia(self):
        # --- EFECTO DE DESENFOQUE ---
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)
        
        dlg = DialogoHistorialDia(self)
        qt_exec(dlg)
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)

    def _is_fila_navegacion(self, row):
        return row >= 0 and self.tabla.hasFocus() and row == self.tabla.currentRow()

    def _sync_nav_border_overlay(self):
        if hasattr(self, "_nav_border_overlay"):
            self._nav_border_overlay.sync_and_repaint()

    def _repintar_filas_nav(self, *rows):
        model = self.tabla.model()
        if model is None:
            return
        for r in rows:
            if r is None or r < 0:
                continue
            for c in range(self.tabla.columnCount()):
                self.tabla.update(model.index(r, c))

    def _on_tabla_nav_row_only(self):
        curr = self.tabla.currentRow()
        prev = getattr(self, "_nav_prev_row", -1)
        if prev != curr:
            self._on_tabla_nav_changed(curr, self.tabla.currentColumn(), prev, -1)

    def _on_tabla_nav_changed(self, current_row=-1, current_col=-1, prev_row=-1, prev_col=-1):
        if current_row < 0:
            current_row = self.tabla.currentRow()
        if prev_row < 0 and hasattr(self, "_nav_prev_row"):
            prev_row = self._nav_prev_row
        self._nav_prev_row = current_row

        for i in range(self.tabla.rowCount()):
            self._reaplicar_estilo_fila(i)

        self._repintar_filas_nav(prev_row, current_row)
        self._sync_nav_border_overlay()

    def _reaplicar_estilo_fila(self, row):
        try:
            desc_val = parse_float_safe(self.tabla.item(row, 4).text())
        except Exception:
            desc_val = 0.0
            
        is_oferta = desc_val > 0
        is_ultimo = (row == getattr(self, "last_active_row", -1))
        is_nav = self._is_fila_navegacion(row)
        activa = is_ultimo or is_nav
        
        if activa:
            bg_color = QColor(SCAN_ROW_BG)
        elif is_oferta:
            bg_color = QColor("#FFEDD5")
        else:
            bg_color = QColor("#FFFFFF") if row % 2 == 0 else QColor("#F8FAFC")
            
        for col in range(self.tabla.columnCount()):
            it = self.tabla.item(row, col)
            if not it: continue
            
            if col == 5:
                it.setBackground(QColor("#D1FAE5") if activa else QColor("#F0FAF4"))
            else:
                it.setBackground(bg_color)
            
            f = it.font()
            f.setBold(True)
            f.setPointSize(20 if activa else 16)
            it.setFont(f)
            
            if col == 1:
                it.setForeground(QColor("#1E3A8A") if activa else (QColor("#C2410C") if is_oferta else QColor("#1E3A8A")))
            elif col == 4:
                it.setForeground(QColor("#1E3A8A") if activa else (QColor("#EA580C") if is_oferta else QColor("#EF4444")))
            elif col == 5:
                it.setForeground(QColor("#047857"))
            else:
                it.setForeground(QColor("#1E3A8A") if activa else (QColor("#C2410C") if is_oferta else QColor("#1E293B")))



if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # Mocking config for direct run
    try:
        from src.config import config
        config.current_user = {"username": "TEST_USER", "role": "admin"}
    except: pass
    win = Paso5Terminal()
    win.showMaximized()
    sys.exit(qt_exec(app))
