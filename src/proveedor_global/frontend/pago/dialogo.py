"""El pago: monto, medio, fecha y una nota. No es solo el número."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
)

from src.contabilidad.shared_globals import date_field, PAL
from src.proveedor_global.backend.cuenta import medios
from src.proveedor_global.backend.moneda import leer, texto


def pedir_pago(parent, restante, proveedor="", varios=1):
    """None si cancela. Si hay varias cuentas, el monto de cada una es su restante."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Registrar pago")
    dlg.setMinimumWidth(440)
    dlg.setStyleSheet("QDialog { background: #F8FAFC; }")
    caja = QVBoxLayout(dlg)
    caja.setContentsMargins(22, 18, 22, 16)
    caja.setSpacing(10)

    titulo = QLabel("Registrar pago" if varios <= 1 else f"Registrar {varios} pagos")
    titulo.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A; background: transparent;")
    caja.addWidget(titulo)
    quien = QLabel(proveedor or "Proveedor")
    quien.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569; background: transparent;")
    caja.addWidget(quien)
    saldo = QLabel(f"Restante {texto(restante)}")
    saldo.setStyleSheet("font-size: 13px; color: #1E293B; background: transparent;")
    caja.addWidget(saldo)

    monto = None
    if varios <= 1:
        caja.addWidget(_rotulo("Monto"))
        monto = QLineEdit()
        monto.setText(f"{float(restante or 0):.2f}")
        monto.setFixedHeight(36)
        monto.setStyleSheet(_campo())
        caja.addWidget(monto)

    caja.addWidget(_rotulo("Forma de pago"))
    medio = QComboBox()
    medio.addItems(list(medios()))
    medio.setFixedHeight(36)
    medio.setStyleSheet(_campo())
    caja.addWidget(medio)

    caja.addWidget(_rotulo("Fecha de emisión"))
    fecha = date_field()
    fecha.setFixedHeight(36)
    caja.addWidget(fecha)

    caja.addWidget(_rotulo("Nota"))
    nota = QLineEdit()
    nota.setPlaceholderText("Detalle o quién pagó")
    nota.setFixedHeight(36)
    nota.setStyleSheet(_campo())
    caja.addWidget(nota)

    pie = QHBoxLayout()
    pie.addStretch()
    cancelar = QPushButton("Cancelar")
    cancelar.setFixedHeight(36)
    cancelar.setStyleSheet(
        "QPushButton { background: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; "
        "border-radius: 8px; padding: 0 16px; font-weight: 700; }"
    )
    cancelar.clicked.connect(dlg.reject)
    ok = QPushButton("Registrar pago")
    ok.setFixedHeight(36)
    ok.setStyleSheet(
        "QPushButton { background: #059669; color: white; border: none; "
        "border-radius: 8px; padding: 0 16px; font-weight: 700; }"
        "QPushButton:hover { background: #047857; }"
    )
    def _aceptar():
        if varios <= 1:
            valor_local = leer(monto.text())
            if valor_local <= 0 or valor_local - float(restante or 0) > 0.009:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(dlg, "Pago", "El monto tiene que estar entre cero y el restante.")
                return
        dlg.accept()

    ok.clicked.connect(_aceptar)
    pie.addWidget(cancelar)
    pie.addWidget(ok)
    caja.addLayout(pie)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    valor = leer(monto.text()) if varios <= 1 else float(restante or 0)
    return {
        "monto": valor,
        "medio": medio.currentText(),
        "fecha": fecha.date().toString("yyyy-MM-dd"),
        "nota": nota.text().strip(),
    }


def _rotulo(texto_lbl) -> QLabel:
    lbl = QLabel(texto_lbl)
    lbl.setStyleSheet(
        f"font-size: 11px; font-weight: 700; color: {PAL['text2']}; "
        "background: transparent; letter-spacing: 0.4px;"
    )
    return lbl


def _campo() -> str:
    return (
        "QLineEdit, QComboBox { background: white; border: 1px solid #CBD5E1; "
        "border-radius: 8px; padding: 0 10px; color: #0F172A; font-size: 14px; }"
    )
