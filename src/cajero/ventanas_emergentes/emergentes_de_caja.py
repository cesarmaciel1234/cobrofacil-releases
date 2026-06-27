from src.utils.qt_compat import qt_exec
import os, json
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QDoubleSpinBox, QFrame, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from src.config import config
from src.base_de_datos.database import db_manager

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
        self.en_venta = False
        self.deuda_actual = 0.0
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        from src.cajero.paso5cobranza import (
            COBRANZA_DIALOG_ANCHO, COBRANZA_DIALOG_ALTO_FIADO, COBRANZA_DIALOG_ALTO_NORMAL,
            _EXEC,
        )
        self._ancho = COBRANZA_DIALOG_ANCHO
        self._altura_normal = COBRANZA_DIALOG_ALTO_NORMAL
        self._altura_fiado = COBRANZA_DIALOG_ALTO_FIADO
        self.setFixedSize(self._ancho, self._altura_normal)
        self.setStyleSheet(
            f"background: {_EXEC['bg']}; border-radius: 20px; border: 1px solid {_EXEC['border']};"
        )
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 22, 30, 22)
        lay.setSpacing(15)

        lbl = QLabel("💵  INGRESO DE DINERO")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"font-size: 20px; font-weight: 900; color: {_EXEC['navy']}; border: none; letter-spacing: 1px;"
        )
        lay.addWidget(lbl)

        lbl_sub = QLabel("Seleccione el concepto del ingreso físico")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet(
            "font-size: 12px; color: #64748B; font-weight: 600; border: none;"
        )
        lay.addWidget(lbl_sub)
        
        # Grid de opciones 3D
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.btn_cambio = self._crear_btn_opcion("🪙", "CAMBIO", "Fondo Fijo", "#3B82F6")
        self.btn_fiado = self._crear_btn_opcion("👥", "FIADO", "Centro Cobranzas", _EXEC["accent"])
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
        self.stack.setStyleSheet(
            "background: transparent; border: none; border-radius: 12px;"
        )
        
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
        
        # Panel Centro de Cobranzas (F6 → FIADO)
        from src.cajero.paso5cobranza import CentroCobranzasPanel

        panel_fiado = QWidget()
        pf_lay = QVBoxLayout(panel_fiado)
        pf_lay.setContentsMargins(0, 4, 0, 4)
        pf_lay.setAlignment(Qt.AlignCenter)
        self.panel_fiado = CentroCobranzasPanel()
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
        
        btn_ok = QPushButton("CONFIRMAR")
        btn_ok.setStyleSheet(
            f"background: {_EXEC['accent']}; color: white; font-weight: 900; font-size: 14px; "
            "padding: 12px; border-radius: 10px; letter-spacing: 1px;"
        )
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
            self.setFixedSize(self._ancho, self._altura_fiado)
            self.stack.setCurrentIndex(1)
            self.panel_fiado.cargar_clientes_abono()
        else:
            self.setFixedSize(self._ancho, self._altura_normal)
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









