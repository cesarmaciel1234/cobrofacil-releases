import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
    QAbstractItemView, QListWidget, QListWidgetItem, QDialog, QPushButton, QGridLayout,
    QComboBox, QDoubleSpinBox, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QDate, QTime
from PyQt5.QtGui import QColor, QFont
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

try:
    from src.database import db_manager
except ImportError:
    from database import db_manager
from src.cajero.paso7_cierre import Paso7CierreCaja
from src.cajero.paso8_historial import DialogoHistorialDia, fmt_moneda
from src.config import config
from src.hardware.printer import printer_manager
from src.hardware.cash_drawer import drawer_manager

def fmt_moneda_sin_centavos(val):
    try:
        return f"${float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "$0,00"

def parse_float_safe(val_str):
    try:
        clean = val_str.replace("$", "").replace(".", "").replace(",", ".")
        return float(clean)
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

class DialogoEditarCantidad(QDialog):
    def __init__(self, cant_actual, nombre, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(450, 280)
        self.setStyleSheet("""
            QDialog { background-color: white; border: 4px solid #437EE8; border-radius: 12px; }
            QLabel { color: #1e293b; font-weight: 800; font-family: 'Segoe UI'; }
            QDoubleSpinBox { 
                font-size: 50px; 
                padding: 10px; 
                border: 2px solid #cbd5e1; 
                border-radius: 8px; 
                background: #f8fafc;
                color: #1e293b;
            }
            QPushButton { 
                border-radius: 8px; 
                padding: 15px; 
                font-size: 14px; 
                font-weight: bold; 
                letter-spacing: 1px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        lbl_prod = QLabel(f"MODIFICAR: {nombre.upper()}")
        lbl_prod.setAlignment(Qt.AlignCenter)
        lbl_prod.setStyleSheet("font-size: 14px; color: #64748b; border: none;")
        layout.addWidget(lbl_prod)
        
        lbl_title = QLabel("CANTIDAD")
        lbl_title.setStyleSheet("font-size: 24px; color: #1e293b; border: none;")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)
        
        self.spin = QDoubleSpinBox()
        self.spin.setRange(0.001, 9999.999)
        self.spin.setDecimals(3)
        self.spin.setValue(cant_actual)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.setFocus()
        self.spin.selectAll()
        # Estilo para las flechas del spinbox (estilo industrial)
        self.spin.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        layout.addWidget(self.spin)
        
        layout.addSpacing(10)
        
        btns = QHBoxLayout()
        btn_ok = QPushButton("✅ CONFIRMAR (ENTER)")
        btn_ok.setStyleSheet("background: #10B981; color: white;")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("❌ CANCELAR (ESC)")
        btn_cancel.setStyleSheet("background: #ef4444; color: white;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
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
# ESTADO GLOBAL DEL CAJERO ACTIVO
# Determina qué impresora y cajón se usan en cada venta
# ──────────────────────────────────────────────────────────────
class CajeroActivo:
    numero = 1           # 1 o 2
    nombre = "CAJERO"

    @classmethod
    def set(cls, numero):
        from src.config import config
        cls.numero = numero
        cls.nombre = config.get(f"nombre_cajero_{numero}", "CAJERO" if numero == 1 else "AUXILIAR").upper()

    @classmethod
    def printer_key(cls):
        """Retorna la clave de config para la impresora del cajero activo."""
        return "ticket_printer_2" if cls.numero == 2 else "ticket_printer"

    @classmethod
    def get_printer_name(cls):
        from src.config import config as _c
        return _c.get(cls.printer_key(), '')


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

                    
        if entered_pin == pin_valido:
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
    """Diálogo premium para ingresar dinero a la caja (F6) con un diseño visual limpio e industrial."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monto_ingresado = 0.0
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(400, 320)
        self.setStyleSheet("background: white; border-radius: 16px; border: 3px solid #10B981;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 22, 30, 22)
        lay.setSpacing(12)

        lbl = QLabel("💵  INGRESO DE EFECTIVO")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #10B981; border: none;")
        lay.addWidget(lbl)

        lbl_sub = QLabel("Registro manual de ingreso a caja")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748b; font-weight: bold; border: none;")
        lay.addWidget(lbl_sub)

        lbl2 = QLabel("Monto a ingresar ($):")
        lbl2.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border: none;")
        lay.addWidget(lbl2)

        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignCenter)
        self.txt_monto.setStyleSheet("""
            QLineEdit {
                font-size: 36px; font-weight: 900; color: #059669;
                border: 2px solid #cbd5e1; border-radius: 10px;
                padding: 8px; background: #f8fafc;
            }
            QLineEdit:focus { border-color: #10B981; }
        """)
        self.txt_monto.returnPressed.connect(self._procesar)
        lay.addWidget(self.txt_monto)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none;")
        lay.addWidget(self.lbl_err)

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background: #F1F5F9; color: #475569; font-weight: bold; padding: 12px; border-radius: 8px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("🚀 INGRESAR")
        btn_ok.setStyleSheet("background: #10B981; color: white; font-weight: 900; font-size: 15px; padding: 12px; border-radius: 8px;")
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel); h_btns.addWidget(btn_ok)
        lay.addLayout(h_btns)

        QTimer.singleShot(100, self.txt_monto.setFocus)

    def _procesar(self):
        try:
            val = float(self.txt_monto.text().strip())
            if val <= 0:
                self.lbl_err.setText("⚠️ Ingresa un monto mayor a 0")
                return
            self.monto_ingresado = val
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
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
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
        lbl_p1 = QLabel("Perfil Principal\n(Impresora 1)")
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
        lbl_p2 = QLabel("Perfil Secundario\n(Impresora 2)")
        lbl_p2.setAlignment(Qt.AlignCenter)
        lbl_p2.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; background: transparent; border: none;")
        lay_c2.addWidget(lbl_t2); lay_c2.addWidget(lbl_p2)
        self.btn_auxiliar.clicked.connect(lambda: self._pedir_pin(2))

        cards_lay.addWidget(self.btn_cajero)
        cards_lay.addWidget(self.btn_auxiliar)
        main_lay.addLayout(cards_lay)
        
        main_lay.addStretch()

        # Mensaje IA / Aprendizaje
        ai_tip = QLabel("🤖 TIP IA: El nombre del perfil será registrado en cada ticket impreso. Usa [ESC] para mantener bloqueado.")
        ai_tip.setAlignment(Qt.AlignCenter)
        ai_tip.setWordWrap(True)
        ai_tip.setStyleSheet("font-size: 13px; color: #0284C7; font-weight: bold; background: #E0F2FE; padding: 12px; border-radius: 8px; border: none;")
        main_lay.addWidget(ai_tip)

    def _pedir_pin(self, numero_cajero):
        from src.config import config
        nombre = config.get(f"nombre_cajero_{numero_cajero}", f"Cajero {numero_cajero}").upper()
        dlg = DialogoPIN(nombre, parent=self)
        if dlg.exec_() and dlg.ok:
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
    """
    PASO 5: TERMINAL INDUSTRIAL EXACTA (100% Foto + Búsqueda Rápida)
    """
    def __init__(self):
        super().__init__()
        self.txt_scan = None
        self.setup_ui()
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
        
        # Monitor de Seguridad: Delegado al Motor Global en MainWindow
        pass

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
            import uuid
            caja_id = config.get("caja_id", 1)
            try:
                ip = socket.gethostbyname(socket.gethostname())
            except:
                ip = "127.0.0.1"
            hostname = f"{socket.gethostname().upper()} [{ip}]"
            hardware_id = f"{uuid.getnode():012X}_{numero_cajero}"
            
            
            numero_cajero = CajeroActivo.get()
            cajero_name = config.get(f"nombre_cajero_{numero_cajero}", "CAJERO")
            
            # Registrar presencia de este terminal
            db_manager.registrar_heartbeat(hardware_id, caja_id, hostname, cajero_name)
            
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
                try:
                    ip = socket.gethostbyname(socket.gethostname())
                except:
                    ip = "127.0.0.1"
                hostname = f"{socket.gethostname().upper()} [{ip}]"
                self.lbl_caja_num.setText(f"Caja №:        [{caja_id:02d}]{hostname}  (Desconectado)")
            except Exception:
                self.lbl_caja_num.setText("Caja №:        Desconectado")

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
                self.tabla.item(i, 2).setText(f"{p_final:.2f}")
                self.tabla.item(i, 4).setText(f"{desc:.2f}")
                self.tabla.item(i, 5).setText(f"{cant * p_final:.2f}")
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
        self.header_frame.setFixedHeight(75)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #3B82F6); 
                color: white; 
                border-radius: 12px;
            }
            QLabel { background: transparent; color: #F8FAFC; }
        """)
        header_layout = QHBoxLayout(self.header_frame)
        
        col1 = QVBoxLayout(); col1.setSpacing(0)
        self.lbl_estado = QLabel("Estado:           MAESTRA")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_instalacion = QLabel("№ 0000-0000-0000")
        self.lbl_instalacion.setStyleSheet("font-weight: bold; font-size: 14px;")
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
        self.lbl_caja_num.setStyleSheet("font-weight: bold; font-size: 14px;")
        row_caja.addWidget(self.lbl_caja_num)
        row_caja.addStretch()
        
        col2.addLayout(row_caja)
        
        self.lbl_fecha = QLabel(f"Fecha:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.lbl_fecha.setStyleSheet("font-weight: bold; font-size: 14px;")
        col2.addWidget(self.lbl_fecha)
        header_layout.addLayout(col2)
        
        header_layout.addStretch()
        
        title = config.get('business_name', 'Punto de Venta [20.09.02]')
        self.lbl_terminal_title = QLabel(title)
        self._orig_title = title
        self.lbl_terminal_title.setStyleSheet("font-size: 26px; font-weight: bold;")
        header_layout.addWidget(self.lbl_terminal_title)
        self.main_layout.addWidget(self.header_frame)
        
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
                font-size: 19px; 
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
                background-color: #1E3A8A; 
                color: #FFFFFF;
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
        self.tabla.setColumnWidth(0, 100) # ID / Barcode (100px)
        self.tabla.setColumnWidth(2, 200) # PRECIO (200px)
        self.tabla.setColumnWidth(3, 200) # CANT (200px)
        self.tabla.setColumnWidth(4, 300) # DES. TOTAL (300px)
        self.tabla.setColumnWidth(5, 300) # SUBTOTAL (300px)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(55) # Mayor respiro para los items (Evita que estén muy unidos)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.installEventFilter(self) # BINDING INDUSTRIAL PARA ENTER EN LA TABLA
        central_layout.addWidget(self.tabla)
        
        self.main_layout.addWidget(self.central_frame)

        # --- BOTTOM DASHBOARD ---
        self.dashboard_frame = QFrame()
        self.dashboard_frame.setFixedHeight(140)
        self.dashboard_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border: 1px solid #CBD5E1;")
        dash_layout = QHBoxLayout(self.dashboard_frame)
        dash_layout.setContentsMargins(10, 5, 10, 5)
        
        # F1-Barcode
        f1_box = QFrame()
        f1_box.setFixedWidth(420)
        f1_box.setStyleSheet("border: none;")
        f1_l = QVBoxLayout(f1_box)
        f1_l.setContentsMargins(5, 15, 5, 15)
        f1_l.setSpacing(0)
        
        self.txt_scan = QLineEdit()
        self.txt_scan.setPlaceholderText("🔍 Código o Producto (F1)...")
        self.txt_scan.setStyleSheet("""
            QLineEdit {
                background: white; border: 3px solid #3B82F6; border-radius: 12px; 
                color: #1E3A8A; font-size: 34px; padding: 12px; font-weight: 900;
            }
        """)
        
        # Efecto de Brillo Industrial (Neon Glow)
        glow = QGraphicsDropShadowEffect(self.txt_scan)
        glow.setBlurRadius(20)
        glow.setColor(QColor(59, 130, 246, 150))
        glow.setOffset(0, 0)
        self.txt_scan.setGraphicsEffect(glow)

        self.txt_scan.textChanged.connect(self.actualizar_busqueda)
        self.txt_scan.returnPressed.connect(self.procesar_scan)
        
        f1_l.addWidget(self.txt_scan)
        dash_layout.addWidget(f1_box)
        
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
        self.lbl_total_val.setStyleSheet("font-size: 75px; color: #059669; font-weight: 900; border: none;")
        self.lbl_total_val.setAlignment(Qt.AlignRight)
        
        # Agrupar Ahorro y Total lado a lado en un contenedor horizontal perfectamente centrado verticalmente
        self.totales_container = QHBoxLayout()
        self.totales_container.setSpacing(35)
        self.totales_container.addWidget(self.lbl_total_val, alignment=Qt.AlignVCenter)
        self.totales_container.addWidget(self.lbl_ahorro_val, alignment=Qt.AlignVCenter)
        dash_layout.addLayout(self.totales_container)
        
        dash_layout.addSpacing(10)
        
        # Sidebar Resumen (Persistencia de última venta)
        side_box = QFrame()
        side_box.setFixedWidth(240)
        side_box.setStyleSheet("""
            QFrame {
                background: #f8fafc; 
                border: 1px solid #e2e8f0; 
                border-radius: 12px;
            }
            QLabel { border: none; background: transparent; }
        """)
        sl = QVBoxLayout(side_box)
        sl.setContentsMargins(15, 10, 15, 10)
        sl.setSpacing(5)
        
        self.lbl_side_cant = QLabel("CANTIDAD:       0.00")
        self.lbl_side_total = QLabel("TOTAL VENTA:    0.00")
        self.lbl_side_pagos = QLabel("PAGOS:          0.00")
        self.lbl_side_cambio = QLabel("CAMBIO:         0.00")
        
        for l in [self.lbl_side_cant, self.lbl_side_total, self.lbl_side_pagos, self.lbl_side_cambio]:
            l.setStyleSheet("font-size: 14px; color: #475569; font-weight: 800; font-family: 'Consolas', monospace;")
            sl.addWidget(l)
            
        # Resaltar Cambio
        self.lbl_side_cambio.setStyleSheet("font-size: 16px; color: #10b981; font-weight: 900; font-family: 'Consolas', monospace;")
        
        dash_layout.addWidget(side_box)
        
        self.en_venta = False
        self.main_layout.addWidget(self.dashboard_frame)
        
        # --- BARRA DE ESTADO / COMANDOS (EL PISO) ---
        status_bar = QFrame()
        status_bar.setFixedHeight(35)
        status_bar.setStyleSheet("background: #0F172A; border-top: 1px solid #334155;")
        sl = QHBoxLayout(status_bar); sl.setContentsMargins(15, 0, 5, 0)
        
        self.lbl_version = QLabel("🚀 CajaFacil Pro v2026.0 | TERMINAL ACTIVA")
        self.lbl_version.setStyleSheet("color: #10B981; font-weight: 900; font-size: 11px; letter-spacing: 1px; border: none;") 
        sl.addWidget(self.lbl_version); sl.addStretch()
        
        lbl_hints = QLabel("⌨️  [F1] BUSCAR  |  [F3] HISTORIAL  |  [F4] PAGAR  |  [F5] RETIRO  |  [F6] INGRESO  |  [F8] BLOQ  |  [F12] CIERRE")
        lbl_hints.setStyleSheet("color: #94A3B8; font-weight: 800; font-size: 11px; border: none;")
        sl.addWidget(lbl_hints)

        sl.addSpacing(10)
        # Botón Candado
        self.btn_candado = QPushButton("🔒")
        self.btn_candado.setFixedSize(30, 25)
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
        sl.addSpacing(5)
        
        self.main_layout.addWidget(status_bar)
        self.txt_scan.setFocus()
        QTimer.singleShot(500, self.txt_scan.setFocus) # Asegurar foco inicial
        self.txt_scan.installEventFilter(self) # Para monitoreo PRO

    def mousePressEvent(self, event):
        # Al hacer click en cualquier parte, el cursor vuelve al buscador y se oculta la lista
        if getattr(self, 'list_results', None) is not None and not self.list_results.isHidden():
            self.list_results.hide()
        if getattr(self, 'txt_scan', None) is not None:
            self.txt_scan.setFocus()
        super().mousePressEvent(event)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        
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
                if key == Qt.Key_F12:
                    self.abrir_cierre_caja()
                    return True  # Consumir el evento, no propagarlo
                elif key == Qt.Key_F3:
                    self.abrir_historial_dia()
                    return True
                elif key == Qt.Key_F4:
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
                        return True
                elif key == Qt.Key_Up:
                    if self.tabla.rowCount() > 0:
                        self.tabla.setFocus()
                        self.tabla.selectRow(self.tabla.rowCount() - 1)
                        self.tabla.setCurrentCell(self.tabla.rowCount() - 1, 3)
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
            if event.type() == QEvent.KeyPress:
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    row = self.tabla.currentRow()
                    if row != -1:
                        nombre = self.tabla.item(row, 1).text()
                        cant_actual = float(self.tabla.item(row, 3).text())
                        
                        dlg = DialogoEditarCantidad(cant_actual, nombre, self)
                        if dlg.exec_():
                            new_cant = dlg.get_value()
                            self.tabla.item(row, 3).setText(f"{new_cant:.2f}")
                            
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
                                        
                                self.tabla.item(row, 2).setText(f"{p_ap:.2f}")
                                self.tabla.item(row, 4).setText(f"{desc_t:.2f}")
                                p_unit = p_ap
                            else:
                                p_unit = float(self.tabla.item(row, 2).text())
                            
                            # Actualizar Subtotal
                            self.tabla.item(row, 5).setText(f"{new_cant * p_unit:.2f}")
                            self._reaplicar_estilo_fila(row)
                            self.actualizar_totales()
                        
                        QTimer.singleShot(50, self.txt_scan.setFocus)
                    return True # Consumido incondicionalmente
                elif event.key() == Qt.Key_Delete:
                    row = self.tabla.currentRow()
                    if row != -1:
                        dlg = DialogoAtencion(self)
                        if dlg.exec_():
                            self.tabla.removeRow(row)
                            self.actualizar_totales()
                        QTimer.singleShot(50, self.txt_scan.setFocus)
                    return True

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

    def _guardar_sesion_cajero(self, numero_cajero):
        self.sesiones_cajero[numero_cajero] = {
            'cart': list(self.productos_en_ticket),
            'total': self.total
        }

    def _cargar_sesion_cajero(self, numero_cajero):
        sesion = self.sesiones_cajero[numero_cajero]
        self.productos_en_ticket = list(sesion['cart'])
        self.total = sesion['total']
        
        self.tabla.setRowCount(0)
        for i, it in enumerate(self.productos_en_ticket):
            self.tabla.insertRow(i)
            # Recrear celdas
            from PyQt5.QtWidgets import QTableWidgetItem, QPushButton
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QColor, QFont
            
            c0 = QTableWidgetItem(str(it['cant']))
            c0.setTextAlignment(Qt.AlignCenter)
            c0.setFont(QFont("Inter", 12, QFont.Bold))
            
            c1 = QTableWidgetItem(it['nombre'])
            if "🔥" in it['nombre'] or "🏷️" in it['nombre']:
                c1.setForeground(QColor("#059669"))
            c1.setFont(QFont("Inter", 10, QFont.Bold))
            
            c2 = QTableWidgetItem(f"")
            c2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            c3 = QTableWidgetItem(f"")
            c3.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            c3.setFont(QFont("Inter", 11, QFont.Bold))
            
            # Botón Eliminar
            btn_del = QPushButton("🗑️")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 14px; } QPushButton:hover { background: #fee2e2; border-radius: 4px; }")
            btn_del.clicked.connect(lambda ch, row=i: self.eliminar_fila(row))
            
            self.tabla.setItem(i, 0, c0)
            self.tabla.setItem(i, 1, c1)
            self.tabla.setItem(i, 2, c2)
            self.tabla.setItem(i, 3, c3)
            self.tabla.setCellWidget(i, 4, btn_del)
            
        self.lbl_total.setText(f"")

    def bloquear_terminal(self):
        """Bloquea la terminal. Al desbloquear, el cajero seleccionado queda activo con su propio carrito."""
        from PyQt5.QtWidgets import QGraphicsBlurEffect
        
        # 1. Guardar la sesión del cajero ACTUAL antes de bloquear
        cajero_anterior = CajeroActivo.numero
        self._guardar_sesion_cajero(cajero_anterior)
        
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(15)
        self.setGraphicsEffect(blur_effect)
        
        dlg = DialogoCandado(parent=self)
        dlg.exec_()   # Si no se desbloquea, la terminal queda bloqueada
        
        self.setGraphicsEffect(None)

        # 2. Si el cajero cambió, cargar su carrito independiente
        cajero_nuevo = CajeroActivo.numero
        if cajero_anterior != cajero_nuevo:
            self._cargar_sesion_cajero(cajero_nuevo)

        # Actualizar barra de estado según el cajero activo
        self._actualizar_barra_cajero()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self.txt_scan.setFocus)

    def _actualizar_barra_cajero(self):
        """Refresca el label de la barra de estado con el cajero activo."""
        nombre_str = CajeroActivo.nombre.upper()
        if CajeroActivo.numero == 2:
            self.lbl_version.setText(f"🟢 {nombre_str}  |  CajaFacil Pro v2026.0")
            self.lbl_version.setStyleSheet("color: #10b981; font-weight: 900; font-size: 11px; letter-spacing: 1px; border: none;")
            self.btn_candado.setStyleSheet("""
                QPushButton {
                    background: #059669; color: white; border-radius: 5px;
                    font-size: 14px; font-weight: bold; border: 1px solid #10b981;
                }
                QPushButton:hover { background: #EF4444; border-color: #EF4444; }
            """)
        else:
            self.lbl_version.setText(f"🔵 {nombre_str}  |  CajaFacil Pro v2026.0")
            self.lbl_version.setStyleSheet("color: #60a5fa; font-weight: 900; font-size: 11px; letter-spacing: 1px; border: none;")
            self.btn_candado.setStyleSheet("""
                QPushButton {
                    background: #1E3A8A; color: white; border-radius: 5px;
                    font-size: 14px; font-weight: bold; border: 1px solid #3B82F6;
                }
                QPushButton:hover { background: #EF4444; border-color: #EF4444; }
            """)




    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Hacer la ventana emergente extra ancha (900x350) para que el código no oculte el nombre
        if hasattr(self, 'dashboard_frame') and hasattr(self, 'list_results'):
            self.list_results.setGeometry(self.dashboard_frame.x() + 10, self.height() - 180 - 360, 900, 350)

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
            from PyQt5.QtWidgets import QApplication
            if QApplication.activeModalWidget() is not None:
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
        from PyQt5.QtWidgets import QMessageBox, QApplication
        
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
                "SELECT id, observaciones FROM movimientos_caja WHERE tipo = 'SOLICITUD_CIERRE' AND caja_id = ? AND observaciones NOT LIKE '%PROCESADO%' AND fecha >= ? ORDER BY id DESC LIMIT 1",
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
                from PyQt5.QtWidgets import QMessageBox
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
        txt = self.txt_scan.text().strip()
        if not txt: self.finalizar_venta(); return
        
        # Lógica de Multiplicador (Ej: 5*12345)
        cantidad_multiplicador = 1.0
        if '*' in txt:
            partes = txt.split('*', 1)
            try:
                cantidad_multiplicador = float(partes[0].replace(',', '.'))
                txt = partes[1].strip()
                if not txt: return
            except ValueError:
                pass

        # Lógica PRO: Artículo Común intencional usando el prefijo '+'
        if txt.startswith('+'):
            try:
                precio_manual = float(txt[1:].replace(',', '.'))
                p = {"id": "000", "nombre": "ARTICULO COMUN", "precio": precio_manual}
                self.agregar_a_tabla(p, cantidad_multiplicador)
                self.txt_scan.clear()
                self.list_results.hide()
                self.txt_scan.setFocus()
                return
            except ValueError:
                pass # Si escriben "+abc", que siga el flujo y no lo encuentre.
        
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
        res_direct = db_manager.execute_query("SELECT id, nombre, precio, cant_oferta, precio_oferta FROM productos WHERE id = ?", (txt,))
        if res_direct:
            p = res_direct[0]
            self.agregar_a_tabla(p, cantidad_multiplicador)
            self.txt_scan.clear()
            self.list_results.hide()
            self.txt_scan.setFocus()
            return

        # 2. Lógica PRO: Códigos de Balanza (Configuración Dinámica)
        if len(txt) == 13 and txt.isdigit() and config.get("balanza_habilitada", True):
            prefijo_balanza = str(config.get("balanza_prefijo", "20"))
            
            # Soporte para Prefijo 20 (Peso/Importe) y Prefijo 21 (Unidades)
            is_balanza = txt.startswith(prefijo_balanza) or txt.startswith("21")
            
            if is_balanza:
                try:
                    # Extraer PLU
                    p_start = max(0, int(config.get("balanza_plu_inicio", 3)) - 1)
                    p_len   = int(config.get("balanza_plu_largo", 5))
                    plu     = txt[p_start : p_start + p_len]
                    
                    # Extraer Valor
                    v_start = max(0, int(config.get("balanza_val_inicio", 8)) - 1)
                    v_len   = int(config.get("balanza_val_largo", 5))
                    v_raw   = txt[v_start : v_start + v_len]
                    
                    
                    modo = config.get("balanza_modo", "Importe Total ($)")
                    
                    # Buscar el producto por el PLU extraído
                    # Búsqueda flexible: con ceros y sin ceros a la izquierda (ej: '00010' y '10')
                    plu_limpio = plu.lstrip('0')
                    if not plu_limpio: plu_limpio = '0'
                    
                    res = db_manager.execute_query(
                        "SELECT id, nombre, precio, cant_oferta, precio_oferta FROM productos WHERE id = ? OR id = ?", 
                        (plu, plu_limpio)
                    )
                    if res:
                        p = res[0]
                        precio_unitario = float(p['precio'])
                        
                        # --- CÁLCULO DE VALOR SEGÚN PREFIJO ---
                        divisor = int(config.get("balanza_divisor", 1000))
                        
                        if txt.startswith("21"):
                            # MODO UNIDADES: El valor es la cantidad de piezas (ej: 00001 = 1 unidad)
                            cantidad = float(int(v_raw))
                        else:
                            # MODO BALANZA (PESO O IMPORTE)
                            valor_numerico = float(v_raw) / divisor
                            if "Importe" in modo:
                                if precio_unitario > 0:
                                    cantidad = valor_numerico / precio_unitario
                                else:
                                    cantidad = 1.0 # Fallback
                            else:
                                # Modo Peso
                                cantidad = valor_numerico
                        
                        # Cargar a la tabla
                        self.agregar_a_tabla(p, cantidad)
                        
                        self.txt_scan.clear()
                        self.list_results.hide()
                        self.txt_scan.setFocus()
                        return
                    else:
                        # Si el PLU no existe, avisar específicamente
                        from PyQt5.QtWidgets import QMessageBox
                        QMessageBox.warning(self, "Balanza: Producto no encontrado", 
                            f"El código de balanza es correcto, pero el producto con PLU '{plu}' no existe en el sistema.\n\n"
                            "Por favor, asegúrate de crear el producto con ese código en el inventario.")
                        self.txt_scan.selectAll()
                        self.txt_scan.setFocus()
                        return
                except (ValueError, IndexError):
                    pass # Error en parseo, sigue el flujo normal

        # 3. Escaneo directo o búsqueda por nombre (Productos Normales)
        res = db_manager.execute_query("SELECT id, nombre, precio, cant_oferta, precio_oferta FROM productos WHERE id = ? OR nombre LIKE ?", (txt, f"%{txt}%"))

        if res:
            p = res[0]
            self.agregar_a_tabla(p, cantidad_multiplicador)
            self.txt_scan.clear()
            self.list_results.hide()
            self.txt_scan.setFocus()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Encontrado", f"No se encontró ningún producto con el código o nombre: '{txt}'")
            self.txt_scan.selectAll()
            self.txt_scan.setFocus()

    def agregar_a_tabla(self, p, cantidad=1.0):
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
            self.lbl_side_cant.setText(f"CANTIDAD:    {cant:>10.2f}" if cant % 1 != 0 else f"CANTIDAD:    {int(cant):>10,}")
            total_sin = fmt_moneda_sin_centavos(total)
            desc_sin = fmt_moneda_sin_centavos(total_desc)
            if total_desc > 0:
                self.lbl_side_total.setText(f"TOTAL VENTA: {total_sin:>10}\nAHORRO OFER: {desc_sin:>10}")
            else:
                self.lbl_side_total.setText(f"TOTAL VENTA: {total_sin:>10}")
            self.lbl_side_pagos.setText(f"PAGOS:       {'0':>10}")
            self.lbl_side_cambio.setText(f"CAMBIO:      {'0':>10}")
            self.lbl_side_cambio.setStyleSheet("font-size: 14px; color: #475569; font-weight: 800; font-family: 'Consolas', monospace;")
            
        # Gatillar la animación interactiva de ahorro total
        self.animar_ahorro(total_desc)

    def animar_ahorro(self, nuevo_ahorro):
        """ 
        Animación interactiva premium tipo 'saldo ascendente' (+100).
        Incrementa el valor del ahorro de forma asíncrona y fluida usando QVariantAnimation.
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
        
        from PyQt5.QtCore import QVariantAnimation
        if hasattr(self, '_ahorro_anim') and self._ahorro_anim:
            self._ahorro_anim.stop()
            
        self._ahorro_anim = QVariantAnimation(self)
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
        from PyQt5.QtCore import QVariantAnimation, QEasingCurve
        
        if hasattr(self, '_respiracion_anim') and self._respiracion_anim:
            return
            
        self._respiracion_anim = QVariantAnimation(self)
        self._respiracion_anim.setStartValue(0.0)
        self._respiracion_anim.setEndValue(1.0)
        self._respiracion_anim.setDuration(1500) # Ciclo suave de 1.5 segundos
        self._respiracion_anim.setEasingCurve(QEasingCurve.SineCurve)
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
        from PyQt5.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.setGraphicsEffect(blur)
        
        dlg = DialogoRetiroEfectivo(efectivo, parent=self)
        if dlg.exec_() and dlg.monto_retirado > 0:
            # Solicitar PIN de confirmación del operador activo
            pin_dlg = DialogoPIN(CajeroActivo.nombre, parent=self)
            if pin_dlg.exec_() and pin_dlg.ok:
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
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", "No se pudo registrar el retiro en la base de datos.")
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)

    def abrir_ingreso_efectivo(self):
        """Abre el panel de ingreso manual de dinero a la caja (F6)."""
        from PyQt5.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.setGraphicsEffect(blur)
        
        dlg = DialogoIngresoEfectivo(parent=self)
        if dlg.exec_() and dlg.monto_ingresado > 0:
            # Solicitar PIN de confirmación del operador activo
            pin_dlg = DialogoPIN(CajeroActivo.nombre, parent=self)
            if pin_dlg.exec_() and pin_dlg.ok:
                monto = dlg.monto_ingresado
                motivo = getattr(dlg, "motivo", "Ingreso manual de efectivo en terminal")
                usuario = CajeroActivo.nombre
                from src.config import config
                c_id = config.get("caja_id", 1)
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
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso en la base de datos.")
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)

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

        # F4: Cobrar
        if k == Qt.Key_F4:
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

        # F12: Cierre de Caja
        if k == Qt.Key_F12:
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
                    if dlg.exec_():
                        self.tabla.removeRow(row)
                        self.actualizar_totales()
                    QTimer.singleShot(50, self.txt_scan.setFocus)
                    return
                    
                elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    nombre = self.tabla.item(row, 1).text()
                    cant_actual = float(self.tabla.item(row, 3).text())
                    
                    dlg = DialogoEditarCantidad(cant_actual, nombre, self)
                    if dlg.exec_():
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
        from PyQt5.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)
        
        from src.cajero.paso6_cobro import Paso6Cobro
        dlg = Paso6Cobro(total, items, self)
        dlg.descuentaso_oferta = sum(parse_float_safe(self.tabla.item(i, 4).text()) for i in range(self.tabla.rowCount()))
        
        # Ejecutamos el cobro
        ok = dlg.exec_()
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
                # Mostrar resumen de la última venta
                self.lbl_side_total.setText(f"TOTAL VENTA: {fmt_moneda_sin_centavos(res['total']):>10}")
                self.lbl_side_pagos.setText(f"PAGOS:       {fmt_moneda_sin_centavos(res['pago_con']):>10}")
                self.lbl_side_cambio.setText(f"CAMBIO:      {fmt_moneda_sin_centavos(res['cambio']):>10}")
                self.lbl_side_cambio.setStyleSheet("font-size: 16px; color: #10b981; font-weight: 900; font-family: 'Consolas', monospace;")
        else:
            self.flash_feedback(success=False)
            
        QTimer.singleShot(100, self.txt_scan.setFocus)

    def abrir_cierre_caja(self):
        # --- EFECTO DE DESENFOQUE CINEMÁTICO ---
        from PyQt5.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)

        cierre = Paso7CierreCaja(self)
        ok = cierre.exec_()
        
        # Quitamos el desenfoque
        self.setGraphicsEffect(None)

        if ok:
            # Si el cierre fue exitoso, cerramos el turno y volvemos a la pantalla de Perfil/Login
            from PyQt5.QtWidgets import QApplication
            QApplication.exit(888)
        else:
            QTimer.singleShot(50, self.txt_scan.setFocus)

    def abrir_historial_dia(self):
        # --- EFECTO DE DESENFOQUE ---
        from PyQt5.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)
        
        dlg = DialogoHistorialDia(self)
        dlg.exec_()
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)

    def _reaplicar_estilo_fila(self, row):
        try:
            desc_val = parse_float_safe(self.tabla.item(row, 4).text())
        except Exception:
            desc_val = 0.0
            
        is_oferta = desc_val > 0
        is_ultimo = (row == getattr(self, "last_active_row", -1))
        
        # Fondo premium de fila
        if is_ultimo:
            bg_color = QColor("#EFF6FF") # Hermoso fondo azul real suave para el último escaneado
        elif is_oferta:
            bg_color = QColor("#FFEDD5") # Naranja suave para ofertas
        else:
            bg_color = QColor("#FFFFFF") if row % 2 == 0 else QColor("#F8FAFC")
            
        for col in range(self.tabla.columnCount()):
            it = self.tabla.item(row, col)
            if not it: continue
            
            # Reset/Apply background (El subtotal tiene fondo verde agua permanente tipo columna Excel)
            if col == 5:
                it.setBackground(QColor("#D1FAE5") if is_ultimo else QColor("#F0FAF4")) # Verde agua destacado o pastel Excel
            else:
                it.setBackground(bg_color)
            
            # Reapply font settings (El último escaneado tiene letra más grande)
            f = it.font()
            f.setBold(True)
            f.setPointSize(20 if is_ultimo else 16) # 20pt para fila activa y 16pt para el resto
            it.setFont(f)
            
            # Reapply foreground colors based on column type
            if col == 1:
                it.setForeground(QColor("#1E3A8A") if is_ultimo else (QColor("#C2410C") if is_oferta else QColor("#1E3A8A")))
            elif col == 4:
                it.setForeground(QColor("#1E3A8A") if is_ultimo else (QColor("#EA580C") if is_oferta else QColor("#EF4444")))
            elif col == 5:
                it.setForeground(QColor("#047857")) # Verde esmeralda oscuro
            else:
                it.setForeground(QColor("#1E3A8A") if is_ultimo else (QColor("#C2410C") if is_oferta else QColor("#1E293B")))



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # Mocking config for direct run
    try:
        from src.config import config
        config.current_user = {"username": "TEST_USER", "role": "admin"}
    except: pass
    win = Paso5Terminal()
    win.showMaximized()
    sys.exit(app.exec_())

