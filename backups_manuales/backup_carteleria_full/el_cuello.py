"""
El Cuello — Punto de entrada para el lanzador de cartelería TV

Este archivo mantiene compatibilidad con imports existentes reexportando
CarteleriaMainTV como CarteleriaMain.

La lógica real está separada en:
- ui_lanzador_tv.py: Widget Qt con interfaz visual
- cerebro_lanzador_tv.py: Servidor HTTP + navegador kiosk
"""

# Reexportar para compatibilidad con imports existentes
from src.carteleria.lanzador_tv.ui_lanzador_tv import CarteleriaMainTV

# Alias conservado para el registro de pantallas existente.
CarteleriaMain = CarteleriaMainTV

# Reexportar también las clases del cerebro si son necesarias
from src.carteleria.lanzador_tv.cerebro_lanzador_tv import (
    ServidorCuello,
    CarteleriaWebHandler,
    ThreadedHTTPServer
)

__all__ = [
    "CarteleriaMain",  # Alias de CarteleriaMainTV para compatibilidad
    "CarteleriaMainTV",  # Nombre nuevo
    "ServidorCuello",
    "CarteleriaWebHandler",
    "ThreadedHTTPServer",
]
