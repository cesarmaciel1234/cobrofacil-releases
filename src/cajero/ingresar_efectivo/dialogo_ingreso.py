"""Diálogo de Ingreso de Dinero (F6) — Orquestador de paneles."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer

# Importar paneles
from src.cajero.ingresar_efectivo.ingreso_efectivo import PanelIngresoEfectivo
from src.cajero.ingresar_efectivo.fiado import CentroCobranzasPanel, _EXEC
from src.cajero.ingresar_efectivo.otros_ingresos import PanelOtrosIngresos

class DialogoIngresoEfectivo(QDialog):
    """Diálogo contenedor para Cambio, Fiado y Otros ingresos (F6)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monto_ingresado = 0.0
        self.motivo = ""
        self.tipo_ingreso = "FIADO"
        self.cliente_id = None
        self.cliente_nombre = ""
        self.en_venta = False
        self.deuda_actual = 0.0

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Unified size for all panels to prevent layout collapse
        self._ancho = 500
        self._altura = 500
        self.setFixedSize(self._ancho, self._altura)
        
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 3px solid #1E3A8A; border-radius: 18px; }"
        )
        outer.addWidget(self._card)

        lay = QVBoxLayout(self._card)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)

        # Header Title
        lbl = QLabel("💵  INGRESO DE DINERO")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "font-size: 20px; font-weight: 900; color: #1E3A8A; border: none; "
            "letter-spacing: 1px; background: transparent;"
        )
        lay.addWidget(lbl)

        # Tabs Grid
        grid = QGridLayout()
        grid.setSpacing(10)

        self.btn_cambio = self._crear_btn_opcion("🪙", "CAMBIO", "#3B82F6")
        self.btn_fiado = self._crear_btn_opcion("👥", "FIADO", _EXEC["accent"])
        self.btn_otros = self._crear_btn_opcion("📦", "OTROS", "#6366F1")

        self.btn_cambio.clicked.connect(lambda: self._set_modo("CAMBIO"))
        self.btn_fiado.clicked.connect(lambda: self._set_modo("FIADO"))
        self.btn_otros.clicked.connect(lambda: self._set_modo("OTROS"))

        grid.addWidget(self.btn_cambio, 0, 0)
        grid.addWidget(self.btn_fiado, 0, 1)
        grid.addWidget(self.btn_otros, 0, 2)
        lay.addLayout(grid)

        # Stack para paneles
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")

        self.panel_cambio = PanelIngresoEfectivo()
        if hasattr(self.panel_cambio, 'txt_monto'):
            self.panel_cambio.txt_monto.returnPressed.connect(self._procesar)
        
        self.panel_fiado = CentroCobranzasPanel()
        if hasattr(self.panel_fiado, 'txt_monto') and self.panel_fiado.txt_monto is not None:
            self.panel_fiado.txt_monto.returnPressed.connect(self._procesar)
            
        self.panel_otros = PanelOtrosIngresos()
        if hasattr(self.panel_otros, 'txt_monto'):
            self.panel_otros.txt_monto.returnPressed.connect(self._procesar)

        self.stack.addWidget(self.panel_cambio)  # index 0
        self.stack.addWidget(self.panel_fiado)   # index 1
        self.stack.addWidget(self.panel_otros)   # index 2
        lay.addWidget(self.stack)

        # Error label
        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none;")
        lay.addWidget(self.lbl_err)

        # Buttons
        h_btns = QHBoxLayout()
        h_btns.setSpacing(14)

        btn_cancel = QPushButton("  ESC  Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #DC2626; color: white; font-weight: bold; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #B91C1C; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("✅ CONFIRMAR")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: 900; font-size: 14px; "
            "padding: 12px 20px; border-radius: 10px; border: none; letter-spacing: 1px; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel, 1)
        h_btns.addWidget(btn_ok, 1)
        lay.addLayout(h_btns)

        self._set_modo("FIADO")

    def _crear_btn_opcion(self, icono, titulo, color):
        btn = QPushButton()
        btn.setFixedHeight(80)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_i = QLabel(icono)
        lbl_i.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        lbl_i.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("font-weight: 900; font-size: 12px; border: none; background: transparent;")
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(lbl_i)
        lay.addWidget(lbl_t)
        return btn

    def _set_modo(self, modo):
        self.tipo_ingreso = modo
        self.btn_cambio.setChecked(modo == "CAMBIO")
        self.btn_fiado.setChecked(modo == "FIADO")
        self.btn_otros.setChecked(modo == "OTROS")

        self.lbl_err.setText("")
        
        if modo == "CAMBIO":
            self.stack.setCurrentIndex(0)
            self.panel_cambio.reset()
        elif modo == "FIADO":
            self.stack.setCurrentIndex(1)
            self.panel_fiado.cargar_clientes_abono()
        elif modo == "OTROS":
            self.stack.setCurrentIndex(2)
            self.panel_otros.reset()

    def _procesar(self):
        try:
            if self.tipo_ingreso == "CAMBIO":
                ok, err = self.panel_cambio.validar()
                if not ok:
                    self.lbl_err.setText(err)
                    return
                self.monto_ingresado = self.panel_cambio.monto()
                self.motivo = "Ingreso de Cambio / Fondo Fijo"
                
            elif self.tipo_ingreso == "FIADO":
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
                
            elif self.tipo_ingreso == "OTROS":
                ok, err = self.panel_otros.validar()
                if not ok:
                    self.lbl_err.setText(err)
                    return
                self.monto_ingresado = self.panel_otros.monto()
                self.motivo = self.panel_otros.descripcion()

            self.accept()
        except Exception as e:
            self.lbl_err.setText("⚠️ Error interno al procesar el ingreso")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._procesar()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Left:
            if self.tipo_ingreso == "FIADO":
                self._set_modo("CAMBIO")
            elif self.tipo_ingreso == "OTROS":
                self._set_modo("FIADO")
        elif event.key() == Qt.Key_Right:
            if self.tipo_ingreso == "CAMBIO":
                self._set_modo("FIADO")
            elif self.tipo_ingreso == "FIADO":
                self._set_modo("OTROS")
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parent()
        if parent:
            geo = parent.geometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2
            )
        else:
            screen = self.screen().geometry()
            self.move(
                screen.center().x() - self.width() // 2,
                screen.center().y() - self.height() // 2
            )
