from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QWidget, QStackedWidget
from PyQt6.QtCore import Qt, QTimer
from src.cajero.paso6_cobro.widgets.panel_cliente_fiado import PanelClienteFiado

COBRANZA_DIALOG_ANCHO = 450
COBRANZA_DIALOG_ALTO_FIADO = 480
COBRANZA_DIALOG_ALTO_NORMAL = 350

class DialogoRetiroEfectivo(QDialog):
    """Diálogo industrial rápido para retirar efectivo de caja (F5)."""
    def __init__(self, efectivo_actual, parent=None):
        super().__init__(parent)
        self.efectivo_actual = efectivo_actual
        self.monto_retirado = 0.0
        self.motivo = ""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(400, 390)
        self.setObjectName("TerminalDialogoRetiroEfectivo")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 18, 30, 18)
        lay.setSpacing(10)

        lbl = QLabel("💸  RETIRO DE EFECTIVO")
        lbl.setObjectName("DialogoRetiroEfectivoLbl")
        lay.addWidget(lbl)

        lbl_disp = QLabel(f"Disponible en Caja: ${self.efectivo_actual:,.2f}")
        lbl_disp.setObjectName("DialogoRetiroEfectivoDisp")
        lay.addWidget(lbl_disp)

        lbl2 = QLabel("Monto a retirar ($):")
        lbl2.setObjectName("DialogoRetiroEfectivoLbl2")
        lay.addWidget(lbl2)

        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sugerido = max(0.0, self.efectivo_actual - 40000) if self.efectivo_actual > 50000 else 0.0
        if sugerido > 0:
            self.txt_monto.setText(f"{int(sugerido)}")
        self.txt_monto.setObjectName("DialogoRetiroEfectivoMonto")
        lay.addWidget(self.txt_monto)

        lbl_m = QLabel("Motivo / Descripción (Opcional):")
        lbl_m.setObjectName("DialogoRetiroEfectivoMotivoLbl")
        lay.addWidget(lbl_m)

        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText("Ej: Pago proveedor, Viáticos...")
        self.txt_motivo.setObjectName("DialogoRetiroEfectivoMotivoTxt")
        self.txt_motivo.returnPressed.connect(self._procesar)
        self.txt_monto.returnPressed.connect(self.txt_motivo.setFocus)
        lay.addWidget(self.txt_motivo)

        self.lbl_err = QLabel("")
        self.lbl_err.setObjectName("DialogoRetiroEfectivoError")
        lay.addWidget(self.lbl_err)

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("DialogoRetiroEfectivoCancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("🚀 RETIRAR")
        btn_ok.setObjectName("DialogoRetiroEfectivoOk")
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel)
        h_btns.addWidget(btn_ok)
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
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self._ancho = COBRANZA_DIALOG_ANCHO
        self._altura_normal = COBRANZA_DIALOG_ALTO_NORMAL
        self._altura_fiado = COBRANZA_DIALOG_ALTO_FIADO
        self.setFixedSize(self._ancho, self._altura_normal)
        self.setObjectName("TerminalDialogoIngresoEfectivo")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 22, 30, 22)
        lay.setSpacing(15)

        lbl = QLabel("💵  INGRESO DE DINERO")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setObjectName("DialogoIngresoEfectivoLbl")
        lay.addWidget(lbl)

        lbl_sub = QLabel("Seleccione el concepto del ingreso físico")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setObjectName("DialogoIngresoEfectivoSub")
        lay.addWidget(lbl_sub)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.btn_cambio = self._crear_btn_opcion("🪙", "CAMBIO", "Fondo Fijo", "TerminalIngresoBtnCambio")
        self.btn_fiado = self._crear_btn_opcion("👥", "FIADO", "Centro Cobranzas", "TerminalIngresoBtnFiado")
        self.btn_otros = self._crear_btn_opcion("📦", "OTROS", "Varios", "TerminalIngresoBtnOtros")
        
        self.btn_cambio.clicked.connect(lambda: self._set_modo("CAMBIO"))
        self.btn_fiado.clicked.connect(lambda: self._set_modo("FIADO"))
        self.btn_otros.clicked.connect(lambda: self._set_modo("OTROS"))
        
        grid.addWidget(self.btn_cambio, 0, 0)
        grid.addWidget(self.btn_fiado, 0, 1)
        grid.addWidget(self.btn_otros, 0, 2)
        lay.addLayout(grid)
        
        self.stack = QStackedWidget()
        self.stack.setObjectName("DialogoIngresoEfectivoStack")
        
        panel_normal = QWidget()
        pn_lay = QVBoxLayout(panel_normal)
        pn_lay.setContentsMargins(20, 20, 20, 20)
        self.lbl_titulo_monto = QLabel("Monto a ingresar ($):")
        self.lbl_titulo_monto.setObjectName("DialogoIngresoEfectivoTituloMonto")
        pn_lay.addWidget(self.lbl_titulo_monto)
        
        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto.setObjectName("DialogoIngresoEfectivoMontoTxt")
        self.txt_monto.returnPressed.connect(self._procesar)
        pn_lay.addWidget(self.txt_monto)
        
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Descripción (Opcional)...")
        self.txt_desc.setObjectName("DialogoIngresoEfectivoDesc")
        pn_lay.addWidget(self.txt_desc)
        self.stack.addWidget(panel_normal)
        
        panel_fiado = QWidget()
        pf_lay = QVBoxLayout(panel_fiado)
        pf_lay.setContentsMargins(0, 4, 0, 4)
        pf_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.panel_fiado = PanelClienteFiado()
        if hasattr(self.panel_fiado, 'txt_monto') and self.panel_fiado.txt_monto is not None:
            self.panel_fiado.txt_monto.returnPressed.connect(self._procesar)
        pf_lay.addWidget(self.panel_fiado)
        self.stack.addWidget(panel_fiado)
        
        lay.addWidget(self.stack)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_err.setObjectName("DialogoIngresoEfectivoError")
        lay.addWidget(self.lbl_err)

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("DialogoIngresoEfectivoCancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("CONFIRMAR")
        btn_ok.setObjectName("DialogoIngresoEfectivoOk")
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel)
        h_btns.addWidget(btn_ok)
        lay.addLayout(h_btns)

        self._set_modo("CAMBIO")
        QTimer.singleShot(100, self.txt_monto.setFocus)

    def _crear_btn_opcion(self, icono, titulo, subtitulo, object_name):
        btn = QPushButton()
        btn.setFixedHeight(80)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setObjectName(object_name)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        
        lay = QVBoxLayout(btn)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_i = QLabel(icono)
        lbl_i.setObjectName("DialogoIngresoEfectivoOpcionIcono")
        lbl_i.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_t = QLabel(titulo)
        lbl_t.setObjectName("DialogoIngresoEfectivoOpcionTitulo")
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
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
