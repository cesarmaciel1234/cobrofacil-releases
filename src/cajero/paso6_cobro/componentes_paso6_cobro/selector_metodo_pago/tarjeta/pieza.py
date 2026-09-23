"""Una tarjeta. El clic avisa. No elige el cobro."""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.ruta import carpeta_assets
from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.tarjeta.hoja import (
    estilo_tarjeta,
)

def armar_tarjeta(icono, texto, clave, oscuro, al_click, ancho=280, alto=220):
    marco = QFrame()
    marco.setObjectName("Paso6TarjetaMetodo")
    marco.setFixedSize(ancho, alto)
    marco.setCursor(Qt.CursorShape.PointingHandCursor)
    marco.setStyleSheet(estilo_tarjeta(oscuro))
    marco.setProperty("active", False)

    caja = QVBoxLayout(marco)
    caja.setContentsMargins(12, 16, 12, 12)
    caja.setSpacing(6)

    dibujo_w = max(84, int(ancho * 0.46))
    dibujo_h = max(72, int(alto * 0.46))
    dibujo = QLabel()
    dibujo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ruta = os.path.join(carpeta_assets(), f"{clave.lower()}.png")
    if os.path.exists(ruta):
        dibujo.setPixmap(
            QPixmap(ruta).scaled(
                dibujo_w,
                dibujo_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        dibujo.setStyleSheet("background: transparent; border: none;")
    else:
        dibujo.setText(icono)
        dibujo.setStyleSheet(
            f"font-size: {max(36, int(alto * 0.28))}px; background: transparent; border: none;"
        )

    color = "#F8FAFC" if oscuro else "#0F172A"
    fuente = 24 if ancho >= 240 else 20
    nombre = QLabel(texto.upper())
    nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    nombre.setStyleSheet(
        f"font-size: {fuente}px; font-weight: 700; color: {color}; "
        "background: transparent; border: none; letter-spacing: 0.8px;"
    )

    caja.addWidget(dibujo)
    caja.addWidget(nombre)

    toque = QPushButton(marco)
    toque.setFixedSize(ancho, alto)
    toque.setStyleSheet("background: transparent; border: none;")
    toque.setCursor(Qt.CursorShape.PointingHandCursor)
    toque.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    toque.clicked.connect(lambda _marcado=False, k=clave: al_click(k))

    return {
        "frame": marco,
        "lbl_text": nombre,
        "overlay": toque,
        "icono": (dibujo_w, dibujo_h),
    }
