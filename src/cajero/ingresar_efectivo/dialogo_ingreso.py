"""Diálogo de Ingreso de Dinero (F6) — Estilo global premium."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGridLayout, QFrame, QWidget, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer


class DialogoIngresoEfectivo(QDialog):
    """Diálogo premium para ingresar dinero a la caja (F6)."""
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
        self.setAttribute(Qt.WA_TranslucentBackground)

        from src.cajero.paso5_terminal.paso5cobranza import (
            COBRANZA_DIALOG_ANCHO, COBRANZA_DIALOG_ALTO_FIADO, COBRANZA_DIALOG_ALTO_NORMAL,
            _EXEC,
        )
        self._ancho = COBRANZA_DIALOG_ANCHO
        self._altura_normal = COBRANZA_DIALOG_ALTO_NORMAL
        self._altura_fiado = COBRANZA_DIALOG_ALTO_FIADO
        self._EXEC = _EXEC
        self.setFixedSize(self._ancho, self._altura_normal)
        self._build()

    def _build(self):
        _EXEC = self._EXEC
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 3px solid #1E3A8A; border-radius: 18px; }"
        )
        outer.addWidget(self._card)

        lay = QVBoxLayout(self._card)
        lay.setContentsMargins(30, 22, 30, 22)
        lay.setSpacing(15)

        lbl = QLabel("💵  INGRESO DE DINERO")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            "font-size: 20px; font-weight: 900; color: #1E3A8A; border: none; "
            "letter-spacing: 1px; background: transparent;"
        )
        lay.addWidget(lbl)

        lbl_sub = QLabel("Seleccione el concepto del ingreso físico")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet(
            "font-size: 12px; color: #64748B; font-weight: 600; border: none;"
        )
        lay.addWidget(lbl_sub)

        # Grid de opciones
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
        from src.cajero.paso5_terminal.paso5cobranza import CentroCobranzasPanel

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
        h_btns.setSpacing(14)

        btn_cancel = QPushButton("  ESC  Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: bold; "
            "font-size: 14px; padding: 12px 20px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("✅ CONFIRMAR")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(
            "QPushButton { background: #0D9488; color: white; font-weight: 900; font-size: 14px; "
            "padding: 12px 20px; border-radius: 10px; border: none; letter-spacing: 1px; }"
            "QPushButton:hover { background: #0F766E; }"
        )
        btn_ok.clicked.connect(self._procesar)

        h_btns.addWidget(btn_cancel, 1)
        h_btns.addWidget(btn_ok, 1)
        lay.addLayout(h_btns)

        self._set_modo("CAMBIO")
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

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._procesar()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
