"""Lazy exports: no importar Qt al hacer `from src.carteleria.lanzador_tv import ...`."""

__all__ = [
    "get_lanzador_directo",
    "LanzadorDirectoTV",
    "CarteleriaMainTV",
    "ServidorCuello",
    "CarteleriaWebHandler",
    "ThreadedHTTPServer",
    "WindowManager",
]


def __getattr__(name):
    if name in ("get_lanzador_directo", "LanzadorDirectoTV"):
        from src.carteleria.lanzador_tv.lanzador_directo import (
            LanzadorDirectoTV,
            get_lanzador_directo,
        )
        return get_lanzador_directo if name == "get_lanzador_directo" else LanzadorDirectoTV
    if name == "CarteleriaMainTV":
        from src.carteleria.lanzador_tv.ui_lanzador_tv import CarteleriaMainTV
        return CarteleriaMainTV
    if name in ("ServidorCuello", "CarteleriaWebHandler", "ThreadedHTTPServer"):
        from src.carteleria.lanzador_tv.cerebro_lanzador_tv import (
            CarteleriaWebHandler,
            ServidorCuello,
            ThreadedHTTPServer,
        )
        return {
            "ServidorCuello": ServidorCuello,
            "CarteleriaWebHandler": CarteleriaWebHandler,
            "ThreadedHTTPServer": ThreadedHTTPServer,
        }[name]
    if name == "WindowManager":
        from src.carteleria.lanzador_tv.window_manager import WindowManager
        return WindowManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
