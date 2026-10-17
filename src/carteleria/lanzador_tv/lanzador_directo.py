"""Puerta pública del kiosk. La lógica vive en lanzador_tv/directo/."""

from src.carteleria.lanzador_tv.directo import LanzadorDirectoTV

_lanzador_directo = None


def get_lanzador_directo():
    global _lanzador_directo
    if _lanzador_directo is None:
        _lanzador_directo = LanzadorDirectoTV()
    return _lanzador_directo


__all__ = ["LanzadorDirectoTV", "get_lanzador_directo"]
