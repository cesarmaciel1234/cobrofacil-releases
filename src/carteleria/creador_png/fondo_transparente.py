"""Saca el fondo negro de PNG de vitrina (flood-fill desde los bordes)."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

UMBRAL = 38


def quitar_fondo_negro(path, umbral=UMBRAL):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    pix = img.load()

    def es_fondo(x, y):
        r, g, b, _a = pix[x, y]
        return r <= umbral and g <= umbral and b <= umbral

    visto = bytearray(w * h)
    cola = deque()
    for x, y in (
        (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
        (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2),
    ):
        cola.append((x, y))

    while cola:
        x, y = cola.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        idx = y * w + x
        if visto[idx]:
            continue
        visto[idx] = 1
        if not es_fondo(x, y):
            continue
        r, g, b, _a = pix[x, y]
        pix[x, y] = (r, g, b, 0)
        cola.append((x + 1, y))
        cola.append((x - 1, y))
        cola.append((x, y + 1))
        cola.append((x, y - 1))

    img.save(path, "PNG")
    return path


def procesar_catalogos(carpeta, minimo_bytes=40000):
    root = Path(carpeta)
    if not root.is_dir():
        return []
    hechos = []
    for png in sorted(root.rglob("*.png")):
        if not png.is_file() or png.stat().st_size < minimo_bytes:
            continue
        quitar_fondo_negro(png)
        hechos.append(png.name)
    return hechos
