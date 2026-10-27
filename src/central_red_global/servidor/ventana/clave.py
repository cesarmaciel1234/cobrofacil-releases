"""Clave para apagar el proceso `--server`. No abre la tienda."""

from __future__ import annotations

PIN_DEFECTO = "1234"


def pin_servidor() -> str:
    """La clave guardada, o 1234 si nadie la cambió."""
    try:
        from src.config import config

        pin = config.get("servidor_clave", None)
    except Exception:
        pin = None
    texto = str(pin).strip() if pin is not None else ""
    return texto or PIN_DEFECTO


def pedir_clave(parent, aviso: str = "") -> bool:
    """True solo si escriben la clave. Cancelar o errar no apaga."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
    )

    dialogo = QDialog(parent)
    dialogo.setWindowTitle("Apagar servidor")
    dialogo.setModal(True)
    dialogo.setFixedSize(400, 230)
    dialogo.setStyleSheet(
        """
        QDialog { background: #0F172A; }
        QLabel { color: #E2E8F0; background: transparent; border: none; }
        QLineEdit {
            background: #020617; color: #F8FAFC; border: 1px solid #334155;
            border-radius: 8px; padding: 8px 10px; font-size: 16px;
            font-family: Consolas, 'Cascadia Mono', monospace;
        }
        QPushButton#BtnOk {
            background: #7F1D1D; color: #FEE2E2; border: 1px solid #B91C1C;
            border-radius: 8px; padding: 8px 14px; font-weight: 700;
        }
        QPushButton#BtnNo {
            background: #1E293B; color: #E2E8F0; border: 1px solid #334155;
            border-radius: 8px; padding: 8px 14px; font-weight: 600;
        }
        """
    )

    lay = QVBoxLayout(dialogo)
    lay.setContentsMargins(22, 18, 22, 16)
    lay.setSpacing(8)

    titulo = QLabel("Apagar el servidor")
    titulo.setStyleSheet("font-size: 16px; font-weight: 700; color: #F8FAFC;")
    lay.addWidget(titulo)

    texto_aviso = aviso.strip() or "Escribí la clave del servidor."
    aviso = QLabel(texto_aviso)
    aviso.setWordWrap(True)
    aviso.setStyleSheet("font-size: 12px; color: #94A3B8;")
    lay.addWidget(aviso)

    caja = QLineEdit()
    caja.setEchoMode(QLineEdit.EchoMode.Password)
    caja.setPlaceholderText("Clave")
    lay.addWidget(caja)

    error = QLabel("")
    error.setStyleSheet("font-size: 12px; color: #FCA5A5; font-weight: 600;")
    lay.addWidget(error)

    fila = QHBoxLayout()
    fila.addStretch()
    btn_no = QPushButton("Cancelar")
    btn_no.setObjectName("BtnNo")
    btn_no.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_ok = QPushButton("Apagar")
    btn_ok.setObjectName("BtnOk")
    btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
    fila.addWidget(btn_no)
    fila.addWidget(btn_ok)
    lay.addLayout(fila)

    aceptada = {"ok": False}

    def _probar():
        if caja.text().strip() != pin_servidor():
            error.setText("Clave incorrecta.")
            caja.clear()
            caja.setFocus()
            return
        aceptada["ok"] = True
        dialogo.accept()

    btn_ok.clicked.connect(_probar)
    btn_no.clicked.connect(dialogo.reject)
    caja.returnPressed.connect(_probar)
    caja.setFocus()
    dialogo.exec()
    return aceptada["ok"]
