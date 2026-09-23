"""Las flechas siguen la grilla. No saltan de una punta a la otra."""

from PyQt6.QtCore import Qt

from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.grilla.filas import (
    ABAJO,
    ARRIBA,
)
from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.marco.marcar import (
    marcar_tarjeta,
)

_FLECHAS = (
    Qt.Key.Key_Left,
    Qt.Key.Key_Right,
    Qt.Key.Key_Up,
    Qt.Key.Key_Down,
)


def es_flecha(tecla):
    return tecla in _FLECHAS


def metodo_con_flecha(ventana, tecla):
    actual = ventana.current_metodo if ventana.current_metodo in ARRIBA or ventana.current_metodo in ABAJO else "Efectivo"
    fila = ARRIBA if actual in ARRIBA else ABAJO
    col = fila.index(actual)
    volver = getattr(ventana, "_flecha_volver", None)

    if tecla == Qt.Key.Key_Left:
        ventana._flecha_volver = None
        return fila[max(0, col - 1)]
    if tecla == Qt.Key.Key_Right:
        ventana._flecha_volver = None
        return fila[min(len(fila) - 1, col + 1)]

    if volver and volver[0] == tecla and volver[1] == actual:
        ventana._flecha_volver = None
        return volver[2]

    if tecla == Qt.Key.Key_Down and actual in ARRIBA:
        destino = ABAJO[0 if col <= 1 else 1]
    elif tecla == Qt.Key.Key_Up and actual in ABAJO:
        destino = ARRIBA[0 if col == 0 else 2]
    else:
        destino = actual

    if destino != actual:
        opuesta = Qt.Key.Key_Up if tecla == Qt.Key.Key_Down else Qt.Key.Key_Down
        ventana._flecha_volver = (opuesta, destino, actual)
    return destino


def atender_pagina_metodos(ventana, event):
    """Enter elige. Escape vuelve al carrito. El resto de teclas no pasa."""
    tecla = event.key()
    if event.isAutoRepeat() and not es_flecha(tecla):
        return
    if tecla in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
        if ventana.current_metodo:
            ventana.procesar_click_metodo(ventana.current_metodo)
    elif es_flecha(tecla):
        marcar_tarjeta(ventana, metodo_con_flecha(ventana, tecla))
    elif tecla == Qt.Key.Key_Escape:
        ventana.reject()
    event.accept()
