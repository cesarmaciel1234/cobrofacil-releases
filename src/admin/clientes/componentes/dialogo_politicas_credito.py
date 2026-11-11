"""Configuración y políticas de interés simple por ticket y apalancamiento."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.admin.clientes.theme import _CLI
from src.clientes_fiado.cerebro.cerebro import cerebro
from src.utils.letra import vestir_numero
from src.utils.qt_compat import qt_exec


class DialogoPoliticasCredito(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Políticas de crédito e interés")
        self.setModal(True)
        self.setFixedWidth(520)
        self.setStyleSheet(
            f"QDialog {{ background: white; }} "
            f"QLabel {{ color: {_CLI['text']}; border: none; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        titulo = QLabel("Políticas de crédito e interés")
        titulo.setStyleSheet("font-size: 18px; font-weight: 900;")
        lay.addWidget(titulo)

        explicacion = QLabel(
            "El interés se calcula por ticket sobre el capital pendiente, prorrateado por días.\n"
            "Los motores están completamente separados: si no funciona el contador de interés, "
            "las ventas y la cobranza continúan funcionando con total normalidad."
        )
        explicacion.setWordWrap(True)
        explicacion.setStyleSheet(
            f"color: {_CLI['text_sec']}; font-size: 12px; line-height: 1.4;"
        )
        lay.addWidget(explicacion)

        # Marco de configuración
        form = QFrame()
        form.setStyleSheet(
            f"background: {_CLI['row_alt']}; border: 1px solid {_CLI['border']}; border-radius: 12px;"
        )
        fl = QVBoxLayout(form)
        fl.setContentsMargins(16, 16, 16, 16)
        fl.setSpacing(12)

        # 1. Tasa base mensual
        fila_base = QHBoxLayout()
        lbl_base = QLabel("Interés mensual base")
        lbl_base.setStyleSheet("font-weight: 800; font-size: 13px;")
        lbl_base.setToolTip("Tasa de interés mensual aplicada a cada ticket mientras esté dentro del plazo.")
        self.sp_base = QDoubleSpinBox()
        self.sp_base.setRange(0.0, 50.0)
        self.sp_base.setDecimals(1)
        self.sp_base.setSingleStep(0.5)
        self.sp_base.setSuffix(" %")
        self.sp_base.setMinimumHeight(36)
        self.sp_base.setFixedWidth(110)
        self.sp_base.setValue(float(cerebro.mantenimiento_pct()))
        self.sp_base.valueChanged.connect(self._preview)
        fila_base.addWidget(lbl_base)
        fila_base.addStretch()
        fila_base.addWidget(self.sp_base)
        fl.addLayout(fila_base)

        # 2. Recargo de apalancamiento
        fila_apal = QHBoxLayout()
        lbl_apal = QLabel("Recargo por apalancamiento")
        lbl_apal.setStyleSheet("font-weight: 800; font-size: 13px;")
        lbl_apal.setToolTip("Tasa extra mensual que se suma a la base una vez superado el plazo de días.")
        self.sp_apal = QDoubleSpinBox()
        self.sp_apal.setRange(0.0, 50.0)
        self.sp_apal.setDecimals(1)
        self.sp_apal.setSingleStep(0.5)
        self.sp_apal.setSuffix(" %")
        self.sp_apal.setMinimumHeight(36)
        self.sp_apal.setFixedWidth(110)
        self.sp_apal.setValue(float(cerebro.apalancamiento_pct()))
        self.sp_apal.valueChanged.connect(self._preview)
        fila_apal.addWidget(lbl_apal)
        fila_apal.addStretch()
        fila_apal.addWidget(self.sp_apal)
        fl.addLayout(fila_apal)

        # 3. Días de plazo / corte
        fila_plazo = QHBoxLayout()
        lbl_plazo = QLabel("Plazo de días (gracia)")
        lbl_plazo.setStyleSheet("font-weight: 800; font-size: 13px;")
        lbl_plazo.setToolTip("Cantidad de días corridos antes de aplicar el recargo de apalancamiento.")
        self.sp_plazo = QSpinBox()
        self.sp_plazo.setRange(1, 180)
        self.sp_plazo.setSingleStep(1)
        self.sp_plazo.setSuffix(" días")
        self.sp_plazo.setMinimumHeight(36)
        self.sp_plazo.setFixedWidth(110)
        self.sp_plazo.setValue(int(cerebro.plazo_dias_politica()))
        self.sp_plazo.valueChanged.connect(self._preview)
        fila_plazo.addWidget(lbl_plazo)
        fila_plazo.addStretch()
        fila_plazo.addWidget(self.sp_plazo)
        fl.addLayout(fila_plazo)

        lay.addWidget(form)

        # Cuadro de ejemplo y vista previa en vivo
        self.lbl_preview = QLabel("")
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 12px; "
            f"background: {_CLI['accent_light']}; border: 1px solid #BFDBFE; "
            "border-radius: 10px; padding: 12px; line-height: 1.4;"
        )
        lay.addWidget(self.lbl_preview)
        self._preview()

        # Botones de acción
        botones = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 10px 18px; font-weight: 800; } "
            "QPushButton:hover { background: #E2E8F0; }"
        )
        btn_cancel.clicked.connect(self.reject)
        botones.addWidget(btn_cancel)

        botones.addStretch()

        btn_ok = QPushButton("Guardar políticas")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(
            f"QPushButton {{ background: {_CLI['accent']}; color: white; border: none; "
            "border-radius: 8px; padding: 10px 22px; font-weight: 800; font-size: 13px; }} "
            "QPushButton:hover { background: #2563EB; }"
        )
        btn_ok.clicked.connect(self._guardar)
        botones.addWidget(btn_ok)
        lay.addLayout(botones)

        self._guardado = False

    def _preview(self):
        base = float(self.sp_base.value())
        apal = float(self.sp_apal.value())
        plazo = int(self.sp_plazo.value())
        ejemplo = 100_000.0

        diario_base = base / 30.0
        monto_dia_base = ejemplo * diario_base / 100.0
        acumulado_plazo = monto_dia_base * plazo

        total_moroso = base + apal
        diario_moroso = total_moroso / 30.0
        monto_dia_moroso = ejemplo * diario_moroso / 100.0

        if apal > 0:
            texto = (
                f"<b>Ejemplo para un ticket de $100.000:</b><br>"
                f"• <b>Día 1 al {plazo}:</b> {diario_base:.2f}% diario (${monto_dia_base:,.2f}/d). "
                f"Al día {plazo} acumula <b>${acumulado_plazo:,.2f}</b>.<br>"
                f"• <b>Día {plazo + 1} en adelante:</b> {diario_moroso:.2f}% diario (${monto_dia_moroso:,.2f}/d) "
                f"por apalancamiento ({base:g}% + {apal:g}% = {total_moroso:g}% mensual)."
            )
        else:
            texto = (
                f"<b>Ejemplo para un ticket de $100.000:</b><br>"
                f"• Tasa fija de {diario_base:.2f}% diario (${monto_dia_base:,.2f}/d). "
                f"Sin recargo adicional de apalancamiento."
            )
        self.lbl_preview.setText(texto)

    def _guardar(self):
        from PyQt6.QtWidgets import QMessageBox

        base = self.sp_base.value()
        apal = self.sp_apal.value()
        plazo = self.sp_plazo.value()
        ok, msg = cerebro.guardar_politicas_credito_detalle(base, apal, plazo)
        if ok:
            self._guardado = True
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Políticas de crédito",
                msg or "No se pudo guardar en la PC Maestra. Reintentá con conexión a la tienda.",
            )

    @staticmethod
    def pedir(parent=None) -> bool:
        dlg = DialogoPoliticasCredito(parent)
        qt_exec(dlg)
        return bool(dlg._guardado)
