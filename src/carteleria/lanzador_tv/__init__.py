"""
Lanzador de Cartelería TV — Módulo de UI + Servidor

Estructura:
  - lanzador_directo.py: Lanzador directo sin consola Qt (recomendado)
  - ui_lanzador_tv.py: Widget Qt6 con interfaz visual (modo avanzado)
  - cerebro_lanzador_tv.py: Servidor HTTP + navegador kiosk
  - window_manager.py: Gestión de monitores y atajos F10/F11
  - _preview_tv.py: Vista previa para desarrollo
"""

from .lanzador_directo import get_lanzador_directo, LanzadorDirectoTV
from .ui_lanzador_tv import CarteleriaMainTV
from .cerebro_lanzador_tv import ServidorCuello, CarteleriaWebHandler, ThreadedHTTPServer
from .window_manager import WindowManager

__all__ = [
    "get_lanzador_directo",
    "LanzadorDirectoTV",
    "CarteleriaMainTV",
    "ServidorCuello",
    "CarteleriaWebHandler",
    "ThreadedHTTPServer",
    "WindowManager",
]
