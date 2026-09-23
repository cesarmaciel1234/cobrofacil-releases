"""Enciende el marco del cobro o de la anulación, y lo apaga."""

from PyQt6.QtCore import QTimer

_DURACION_MS = 10000


def _repintar(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def marcar(terminal, estado):
    """aviso: exito, alerta o normal. No usa estado: ese es del cajón y del led."""
    terminal._flash_borde = estado != "normal"
    tabla = getattr(terminal, "componente_tabla", None)
    for widget in (terminal, terminal.dashboard_frame, tabla):
        if widget is None:
            continue
        widget.setProperty("aviso", estado)
        _repintar(widget)


def flash(terminal, success):
    """Verde si el cobro salió. Rojo si se anuló. Diez segundos."""
    marcar(terminal, "exito" if success else "alerta")
    QTimer.singleShot(_DURACION_MS, lambda: marcar(terminal, "normal"))
