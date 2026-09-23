"""Dónde están los dibujos de las tarjetas."""

import os


def carpeta_assets():
    aqui = os.path.abspath(__file__)
    cajero = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(aqui))))
    return os.path.join(cajero, "assets")
