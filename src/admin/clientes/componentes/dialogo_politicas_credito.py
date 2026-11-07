"""Políticas de crédito barrial: % mantenimiento + % apalancamiento."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QPushButton, QFrame,
)

from src.admin.clientes.theme import _CLI
from src.utils.qt_compat import qt_exec


class DialogoPoliticasCredito(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Políticas de crédito")
        self.setModal(True)
        self.setFixedWidth(460)
        self.setStyleSheet(
            f"QDialog {{ background: white; }} "
            f"QLabel {{ color: {_CLI['text']}; border: none; }}"
        )
        from src.clientes_fiado.cerebro.cerebro import cerebro

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        tit = QLabel("Políticas de crédito")
        tit.setStyleSheet("font-size: 17px; font-weight: 900;")
        lay.addWidget(tit)
        sub = QLabel(
            "Mantenimiento sobre la deuda (cuenta en 0 no aplica). "
            "Apalancamiento si pasaron más de 30 días desde el último pago "
            "(pago parcial sí cuenta; si deja en 0 antes del mes, no). "
            "Se aplica al abrir la cartera, máximo una vez cada 30 días."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {_CLI['text_sec']}; font-size: 12px;")
        lay.addWidget(sub)

        form = QFrame()
        form.setStyleSheet(
            f"background: {_CLI['row_alt']}; border: 1px solid {_CLI['border']}; border-radius: 12px;"
        )
        fl = QVBoxLayout(form)
        fl.setContentsMargins(16, 14, 16, 14)
        fl.setSpacing(10)

        fila_base = QHBoxLayout()
        lbl_base = QLabel("Mantenimiento base")
        lbl_base.setStyleSheet("font-weight: 800; font-size: 13px;")
        self.sp_base = QDoubleSpinBox()
        self.sp_base.setRange(0, 15)
        self.sp_base.setDecimals(1)
        self.sp_base.setSuffix(" %")
        self.sp_base.setValue(float(cerebro.mantenimiento_pct()))
        self.sp_base.setMinimumHeight(36)
        self.sp_base.valueChanged.connect(self._preview)
        fila_base.addWidget(lbl_base)
        fila_base.addStretch()
        fila_base.addWidget(self.sp_base)
        fl.addLayout(fila_base)

        fila_apal = QHBoxLayout()
        lbl_apal = QLabel("Apalancamiento (>30 días)")
        lbl_apal.setStyleSheet("font-weight: 800; font-size: 13px;")
        self.sp_apal = QDoubleSpinBox()
        self.sp_apal.setRange(0, 15)
        self.sp_apal.setDecimals(1)
        self.sp_apal.setSuffix(" %")
        self.sp_apal.setValue(float(cerebro.apalancamiento_pct()))
        self.sp_apal.setMinimumHeight(36)
        self.sp_apal.valueChanged.connect(self._preview)
        fila_apal.addWidget(lbl_apal)
        fila_apal.addStretch()
        fila_apal.addWidget(self.sp_apal)
        fl.addLayout(fila_apal)
        lay.addWidget(form)

        self.lbl_preview = QLabel("")
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {_CLI['text']}; "
            f"background: {_CLI['accent_light']}; border-radius: 10px; padding: 12px;"
        )
        lay.addWidget(self.lbl_preview)
        self._preview()

        botones = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Guardar políticas")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(
            f"background: {_CLI['accent']}; color: white; border: none; border-radius: 8px; "
            "padding: 10px 18px; font-weight: 800;"
        )
        btn_ok.clicked.connect(self._guardar)
        botones.addWidget(btn_cancel)
        botones.addStretch()
        botones.addWidget(btn_ok)
        lay.addLayout(botones)

        self._ok = False

    def _preview(self):
        base = float(self.sp_base.value())
        apal = float(self.sp_apal.value())
        ejemplo = 100_000.0
        m_base = ejemplo * base / 100.0
        m_apal = ejemplo * apal / 100.0
        total = m_base + m_apal
        self.lbl_preview.setText(
            f"Ejemplo deuda $100.000 (cuenta en 0 = $0)\n"
            f"Hasta 30 días desde el último pago: solo {base:g}% → ${m_base:,.2f}\n"
            f"Más de 30 días sin saldar: {base:g}% + {apal:g}% = {base + apal:g}% → ${total:,.2f}"
        )

    def _guardar(self):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        if cerebro.guardar_politicas_credito(self.sp_base.value(), self.sp_apal.value()):
            self._ok = True
            self.accept()

    @staticmethod
    def pedir(parent=None) -> bool:
        dlg = DialogoPoliticasCredito(parent)
        qt_exec(dlg)
        return bool(dlg._ok)
