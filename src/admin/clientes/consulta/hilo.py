"""Hilo de admin: pide el historial. Si se cae, la ficha sigue."""

from __future__ import annotations

from PyQt6.QtCore import QCoreApplication, QThread, pyqtSignal

_HILOS_ACTIVOS = set()
_CIERRE_REGISTRADO = False


def iniciar_hilo_seguro(hilo):
    """Conserva el hilo hasta terminar aunque se cierre el diálogo que lo lanzó."""
    global _CIERRE_REGISTRADO

    _HILOS_ACTIVOS.add(hilo)
    hilo.finished.connect(lambda hilo=hilo: _HILOS_ACTIVOS.discard(hilo))
    hilo.finished.connect(hilo.deleteLater)

    app = QCoreApplication.instance()
    if app is not None and not _CIERRE_REGISTRADO:
        app.aboutToQuit.connect(_esperar_hilos_activos)
        _CIERRE_REGISTRADO = True

    hilo.start()
    return hilo


def _esperar_hilos_activos():
    for hilo in tuple(_HILOS_ACTIVOS):
        if hilo.isRunning():
            hilo.wait()
        _HILOS_ACTIVOS.discard(hilo)


class HiloMovimientosAdmin(QThread):
    listo = pyqtSignal(object, str)

    def __init__(self, cliente_id, parent=None):
        super().__init__(None)
        self.cliente_id = cliente_id

    def run(self):
        try:
            from src.clientes_fiado.oficina.consulta_historial.motor import motor_consulta_historial

            self.listo.emit(motor_consulta_historial.movimientos(self.cliente_id), "")
        except Exception as error:
            self.listo.emit([], str(error))
