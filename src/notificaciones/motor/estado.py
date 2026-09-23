"""Avisos temporales. No conoce la pantalla."""

import time

_eventos: list[dict] = []


def publicar(codigo: str, texto: str, segundos: float = 8) -> None:
    try:
        ahora = time.monotonic()
        vivos = [e for e in _eventos if e["hasta"] > ahora and e["codigo"] != codigo]
        vivos.append({"codigo": str(codigo), "texto": str(texto), "hasta": ahora + float(segundos)})
        _eventos[:] = vivos
    except Exception:
        pass


def retirar(codigo: str) -> None:
    try:
        _eventos[:] = [e for e in _eventos if e["codigo"] != codigo]
    except Exception:
        pass


def vigentes() -> list[str]:
    return [e["texto"] for e in vigentes_detalle()]


def vigentes_detalle() -> list[dict]:
    try:
        ahora = time.monotonic()
        return [
            {"codigo": e["codigo"], "texto": e["texto"]}
            for e in _eventos
            if e["hasta"] > ahora
        ]
    except Exception:
        return []
