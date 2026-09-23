"""Pinta el marco de la tarjeta elegida. No abre el cobro ni mueve el foco al monto."""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel

from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.ruta import carpeta_assets


def marcar_tarjeta(ventana, clave):
    ventana.current_metodo = clave
    rotulo = getattr(ventana, "lbl_metodo_activo", None)
    if rotulo is not None:
        rotulo.setText(f"MÉTODO: {clave.upper()}")

    for nombre, pieza in ventana.btns.items():
        activa = nombre == clave
        marco = pieza["frame"]
        marco.setProperty("active", activa)
        marco.style().unpolish(marco)
        marco.style().polish(marco)
        marco.update()

        dibujo = marco.findChild(QLabel)
        if dibujo is not None:
            ruta = os.path.join(carpeta_assets(), f"{nombre.lower()}.png")
            if os.path.exists(ruta):
                base_w, base_h = pieza.get("icono", (120, 100))
                ancho = base_w if activa else int(base_w * 0.84)
                alto = base_h if activa else int(base_h * 0.84)
                dibujo.setPixmap(
                    QPixmap(ruta).scaled(
                        ancho,
                        alto,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.FastTransformation,
                    )
                )

        texto = pieza.get("lbl_text")
        if texto is not None:
            texto.setProperty("type", "metodo_lbl")
            texto.setProperty("active", "true" if activa else "false")
            texto.style().unpolish(texto)
            texto.style().polish(texto)

    pila = getattr(ventana, "stack", None)
    if pila is not None and pila.currentIndex() == 0:
        ventana.setFocus()
