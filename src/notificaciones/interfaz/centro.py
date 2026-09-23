from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout

from src.notificaciones.interfaz.franja import FranjaNotificacion
from src.notificaciones.interfaz.icono import LamparaAlerta, nivel_unico
from src.notificaciones.motor.revisar import revisar_notificaciones


class CentroDeNotificaciones(QFrame):
    """Un mensaje. Las lámparas van en el cabezal, a la derecha."""

    def __init__(self, zona_iconos=None, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalNotificacionesContainer")
        self._zona = zona_iconos
        self._mensaje = None
        self._iconos: tuple = ()
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.franja = FranjaNotificacion(self)
        self._layout.addWidget(self.franja)
        self.hide()

    def refrescar(self):
        try:
            estado = revisar_notificaciones()
        except Exception:
            estado = {"mensaje": None, "iconos": []}
        if not isinstance(estado, dict):
            estado = {"mensaje": None, "iconos": []}
        self._pintar(estado)

    def _pintar(self, estado: dict):
        mensaje = estado.get("mensaje") or None
        iconos = tuple(
            (i.get("codigo"), i.get("nivel"), i.get("detalle") or "Alerta")
            for i in (estado.get("iconos") or [])
            if i.get("codigo") and i.get("nivel") and i.get("detalle")
        )
        if mensaje == self._mensaje and iconos == self._iconos:
            self.show() if mensaje else self.hide()
            return
        self._mensaje = mensaje
        self._iconos = iconos
        if mensaje:
            self.franja.etiqueta.setText(mensaje)
            self.show()
        else:
            self.hide()
        self._pintar_iconos(iconos)

    def _pintar_iconos(self, iconos: tuple):
        zona = self._zona
        if zona is None:
            return
        lay = zona.layout()
        while lay.count():
            item = lay.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not iconos:
            zona.hide()
            return
        nivel = nivel_unico([nivel for _codigo, nivel, _detalle in iconos])
        textos = [detalle for _codigo, _nivel, detalle in iconos]
        lay.addWidget(LamparaAlerta(nivel, textos, zona), 0, Qt.AlignmentFlag.AlignVCenter)
        zona.show()
