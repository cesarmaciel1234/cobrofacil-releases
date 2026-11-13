"""Botón de la ventana: asocia la empresa. El envío lo hace el módulo aparte."""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

_URL_DEFAULT = "https://crm-frigorifico.onrender.com"


def _estilo() -> str:
    return """
    QDialog { background: #0F172A; }
    QLabel { color: #E2E8F0; background: transparent; border: none; }
    QLineEdit {
        background: #020617; color: #F8FAFC; border: 1px solid #334155;
        border-radius: 8px; padding: 8px 10px; font-size: 14px;
    }
    QPushButton#BtnOk {
        background: #1D4ED8; color: #EFF6FF; border: 1px solid #2563EB;
        border-radius: 8px; padding: 8px 14px; font-weight: 700;
    }
    QPushButton#BtnNo {
        background: #1E293B; color: #E2E8F0; border: 1px solid #334155;
        border-radius: 8px; padding: 8px 14px; font-weight: 600;
    }
    """


def _leer_guardado() -> tuple[str, str, str, str, str]:
    try:
        from src.config import config

        url = str(config.get("crm_url") or "").strip()
        clave = str(config.get("crm_password") or config.get("crm_api_key") or "").strip()
        empresa = str(config.get("crm_usuario") or config.get("crm_empresa") or "").strip()
        sucursal_id = str(config.get("crm_sucursal_id") or config.get("sucursal_id") or "1").strip()
        sucursal = str(config.get("crm_sucursal") or "").strip()
    except Exception:
        return _URL_DEFAULT, "", "", "1", ""
    return url or _URL_DEFAULT, clave, empresa, sucursal_id or "1", sucursal


def _guardar(url: str, clave: str, empresa: str, sucursal_id: str, sucursal: str) -> None:
    from src.config import config

    config.set("crm_url", url)
    config.set("crm_usuario", empresa)
    config.set("crm_password", clave)
    config.set("crm_empresa", empresa)
    config.set("crm_sucursal_id", sucursal_id)
    config.set("crm_sucursal", sucursal)


def pedir_acceso(parent) -> tuple[str, str, str, str, str] | None:
    """URL, clave, empresa y sucursal. Cancelar no envía nada."""
    dialogo = QDialog(parent)
    dialogo.setWindowTitle("Enviar cartera al CRM")
    dialogo.setModal(True)
    dialogo.setFixedSize(460, 460)
    dialogo.setStyleSheet(_estilo())

    lay = QVBoxLayout(dialogo)
    lay.setContentsMargins(22, 18, 22, 16)
    lay.setSpacing(8)

    titulo = QLabel("Asociar esta sucursal a la empresa")
    titulo.setStyleSheet("font-size: 16px; font-weight: 700; color: #F8FAFC;")
    lay.addWidget(titulo)

    aviso = QLabel(
        "Escribí el nombre de la empresa, el mismo con el que entra al CRM. "
        "Esta PC, aunque sea esclava, manda la cartera que trajo de la maestra. "
        "Si falla, la tienda sigue."
    )
    aviso.setWordWrap(True)
    aviso.setStyleSheet("font-size: 12px; color: #94A3B8;")
    lay.addWidget(aviso)

    url_guardada, clave_guardada, empresa_guardada, sucursal_id_guardada, sucursal_guardada = _leer_guardado()
    url = QLineEdit(url_guardada)
    url.setPlaceholderText("https://crm-frigorifico.onrender.com")
    lay.addWidget(url)

    clave = QLineEdit(clave_guardada)
    clave.setEchoMode(QLineEdit.EchoMode.Password)
    clave.setPlaceholderText("Contraseña de la empresa")
    lay.addWidget(clave)

    empresa = QLineEdit(empresa_guardada)
    empresa.setPlaceholderText("Nombre de la empresa, por ejemplo maciel")
    lay.addWidget(empresa)

    fila_sucursal = QHBoxLayout()
    sucursal_id = QLineEdit(sucursal_id_guardada)
    sucursal_id.setPlaceholderText("Nº")
    sucursal_id.setFixedWidth(72)
    sucursal = QLineEdit(sucursal_guardada)
    sucursal.setPlaceholderText("Nombre de la sucursal")
    fila_sucursal.addWidget(sucursal_id)
    fila_sucursal.addWidget(sucursal)
    lay.addLayout(fila_sucursal)

    error = QLabel("")
    error.setStyleSheet("font-size: 12px; color: #FCA5A5; font-weight: 600;")
    lay.addWidget(error)

    fila = QHBoxLayout()
    fila.addStretch()
    no = QPushButton("Cancelar")
    no.setObjectName("BtnNo")
    ok = QPushButton("Entrar y enviar")
    ok.setObjectName("BtnOk")
    ok.setDefault(True)
    fila.addWidget(no)
    fila.addWidget(ok)
    lay.addLayout(fila)

    def aceptar() -> None:
        if not url.text().strip() or not clave.text().strip():
            error.setText("Faltan la dirección o la clave.")
            return
        if not empresa.text().strip():
            error.setText("Falta el nombre de la empresa.")
            return
        if not sucursal_id.text().strip().isdigit():
            error.setText("El número de sucursal es un número.")
            return
        if not sucursal.text().strip():
            error.setText("Falta el nombre de la sucursal.")
            return
        dialogo.accept()

    no.clicked.connect(dialogo.reject)
    ok.clicked.connect(aceptar)
    clave.returnPressed.connect(aceptar)
    sucursal.returnPressed.connect(aceptar)
    if dialogo.exec() != QDialog.DialogCode.Accepted:
        return None
    destino = url.text().strip().rstrip("/")
    secreta = clave.text().strip()
    numero_empresa = empresa.text().strip()
    numero_sucursal = sucursal_id.text().strip()
    nombre_sucursal = sucursal.text().strip()
    try:
        _guardar(destino, secreta, numero_empresa, numero_sucursal, nombre_sucursal)
    except Exception:
        logging.getLogger(__name__).warning("No se pudo guardar la clave del CRM")
    return destino, secreta, numero_empresa, numero_sucursal, nombre_sucursal


def conectar(win, consola, boton) -> None:
    """El clic guarda la empresa. El módulo aparte es el que envía."""

    def _aviso(texto: str, nivel: int = logging.INFO) -> None:
        try:
            consola.escribir(texto, nivel)
        except Exception:
            logging.getLogger(__name__).log(nivel, texto)

    def _al_click() -> None:
        acceso = pedir_acceso(win)
        if not acceso:
            return
        url, clave, empresa, sucursal_id, sucursal = acceso
        try:
            _guardar(url, clave, empresa, sucursal_id, sucursal)
        except Exception:
            logging.getLogger(__name__).warning("No se pudo guardar la empresa del CRM")
            _aviso("CRM  no se pudo guardar la empresa", logging.ERROR)
            return
        try:
            from src.central_red_global.servidor.crm_salida.vigilante import pedir_vuelta

            pedir_vuelta()
        except Exception:
            logging.getLogger(__name__).exception("CRM  no despertó el módulo")
        _aviso(
            f"CRM  empresa {empresa} asociada, sucursal {sucursal}. "
            "El módulo la envía, también si esta PC es esclava."
        )

    boton.clicked.connect(_al_click)
