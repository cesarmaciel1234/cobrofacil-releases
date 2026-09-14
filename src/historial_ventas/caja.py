"""Puente al motor del cajero. No se edita paso8."""

from src.cajero.paso8_historial.logica.historial_controller import HistorialController

_caja = HistorialController()


def controller():
    return _caja
