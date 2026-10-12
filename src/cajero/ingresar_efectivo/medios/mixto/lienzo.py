# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QLineEdit, QPushButton, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal

class LienzoMixto(QWidget):
    listo = pyqtSignal(dict)
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(12)

        # Panel principal
        panel = QFrame()
        panel.setStyleSheet("background-color: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 14px;")
        p_lay = QVBoxLayout(panel)
        p_lay.setSpacing(12)
        p_lay.setContentsMargins(24, 16, 24, 16)
        
        # Total a Pagar
        h_tot = QHBoxLayout()
        lbl_t_tag = QLabel("TOTAL A LIQUIDAR:")
        lbl_t_tag.setStyleSheet("color: #475569; font-size: 16px; font-weight: 800;")
        self.lbl_total = QLabel("$0.00")
        self.lbl_total.setStyleSheet("color: #0F172A; font-size: 26px; font-weight: 900;")
        h_tot.addWidget(lbl_t_tag)
        h_tot.addStretch()
        h_tot.addWidget(self.lbl_total)
        p_lay.addLayout(h_tot)
        
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        p_lay.addWidget(linea)

        # Inputs de los 4 medios de pago
        def crear_fila(rotulo, color):
            h = QHBoxLayout()
            lbl = QLabel(rotulo)
            lbl.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {color};")
            lbl.setFixedWidth(130)
            txt = QLineEdit("0,00")
            txt.setAlignment(Qt.AlignmentFlag.AlignRight)
            txt.setStyleSheet(
                f"QLineEdit {{ background: #FFFFFF; color: #0F172A; font-size: 20px; font-weight: 800; "
                f"padding: 6px 12px; border: 2px solid {color}; border-radius: 8px; }}"
            )
            txt.textChanged.connect(self._valor_cambiado)
            txt.returnPressed.connect(lambda c=txt: self._on_enter_campo(c))
            h.addWidget(lbl)
            h.addWidget(txt, 1)
            return h, txt

        h_efec, self.txt_efectivo = crear_fila("Efectivo:", "#10B981")
        h_tarj, self.txt_tarjeta = crear_fila("Tarjeta:", "#3B82F6")
        h_trans, self.txt_transferencia = crear_fila("Transferencia:", "#06B6D4")
        h_qr, self.txt_qr = crear_fila("QR:", "#6366F1")

        p_lay.addLayout(h_efec)
        p_lay.addLayout(h_tarj)
        p_lay.addLayout(h_trans)
        p_lay.addLayout(h_qr)

        lay.addWidget(panel)

        # Botones de Accion
        h_btn = QHBoxLayout()
        h_btn.setSpacing(12)
        
        self.btn_volver = QPushButton("[ ESC ] Volver")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setFixedHeight(48)
        self.btn_volver.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #475569; font-size: 16px; font-weight: 800; "
            "border: 1px solid #CBD5E1; border-radius: 10px; } "
            "QPushButton:hover { background: #E2E8F0; }"
        )
        self.btn_volver.clicked.connect(self.volver.emit)
        
        self.btn_confirmar = QPushButton("[ ENTER ] Confirmar Cobro")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setFixedHeight(48)
        self.btn_confirmar.clicked.connect(self._confirmar)
        
        h_btn.addWidget(self.btn_volver)
        h_btn.addWidget(self.btn_confirmar, 1)
        lay.addLayout(h_btn)
        
        self._monto_total = 0.0
        self._auto_calculando = False

    def arrancar(self, monto):
        self._monto_total = float(monto or 0)
        self.lbl_total.setText(f"${self._monto_total:,.2f}")
        
        self._auto_calculando = True
        self.txt_efectivo.setText(f"{self._monto_total:.2f}".replace('.', ','))
        self.txt_tarjeta.setText("0,00")
        self.txt_transferencia.setText("0,00")
        self.txt_qr.setText("0,00")
        self._auto_calculando = False
        
        self._validar_cobertura()
        self.txt_efectivo.setFocus()
        self.txt_efectivo.selectAll()

    def _parse_val(self, txt):
        try:
            return float(txt.replace('.', '').replace(',', '.') or 0)
        except Exception:
            return 0.0

    def _on_enter_campo(self, campo_actual):
        if self.btn_confirmar.isEnabled():
            self._confirmar()
            return
            
        e = self._parse_val(self.txt_efectivo.text())
        t = self._parse_val(self.txt_tarjeta.text())
        tr = self._parse_val(self.txt_transferencia.text())
        q = self._parse_val(self.txt_qr.text())
        suma = e + t + tr + q
        resto = self._monto_total - suma
        
        campos = [self.txt_efectivo, self.txt_tarjeta, self.txt_transferencia, self.txt_qr]
        try:
            idx = campos.index(campo_actual)
            sig = campos[(idx + 1) % len(campos)]
        except Exception:
            sig = self.txt_qr
            
        if resto > 0.009 and self._parse_val(sig.text()) <= 0.009:
            self._auto_calculando = True
            sig.setText(f"{resto:.2f}".replace('.', ','))
            self._auto_calculando = False
            self._validar_cobertura()
            
        sig.setFocus()
        sig.selectAll()

    def _valor_cambiado(self):
        if self._auto_calculando:
            return
        self._validar_cobertura()

    def _validar_cobertura(self):
        e = self._parse_val(self.txt_efectivo.text())
        t = self._parse_val(self.txt_tarjeta.text())
        tr = self._parse_val(self.txt_transferencia.text())
        q = self._parse_val(self.txt_qr.text())
        
        suma = e + t + tr + q
        resto = self._monto_total - suma
        
        if abs(resto) < 0.01:
            self.btn_confirmar.setText("[ ENTER ] Confirmar Cobro")
            self.btn_confirmar.setStyleSheet(
                "QPushButton { background: #10B981; color: #FFFFFF; font-size: 17px; font-weight: 900; "
                "border: none; border-radius: 10px; } "
                "QPushButton:hover { background: #059669; }"
            )
            self.btn_confirmar.setEnabled(True)
        else:
            if resto > 0:
                self.btn_confirmar.setText(f"Falta cubrir: ${resto:,.2f}")
            else:
                self.btn_confirmar.setText(f"Sobran: ${abs(resto):,.2f}")
            self.btn_confirmar.setStyleSheet(
                "QPushButton:disabled { background: #FEE2E2; color: #DC2626; font-size: 16px; font-weight: 800; "
                "border: 1px solid #FCA5A5; border-radius: 10px; }"
            )
            self.btn_confirmar.setEnabled(False)

    def _confirmar(self):
        e = self._parse_val(self.txt_efectivo.text())
        t = self._parse_val(self.txt_tarjeta.text())
        tr = self._parse_val(self.txt_transferencia.text())
        q = self._parse_val(self.txt_qr.text())
        
        self.listo.emit({
            "Efectivo": e,
            "Tarjeta": t,
            "Transferencia": tr,
            "QR": q
        })
        
    def tecla(self, k):
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.btn_confirmar.isEnabled():
                self._confirmar()
        elif k == Qt.Key.Key_Escape:
            self.volver.emit()
