"""La única puerta. Los otros módulos preguntan acá y no escriben productos."""

from src.motor_inventario.puerta.consultar import catalogo, por_codigo, por_id, precios
from src.motor_inventario.puerta.mandar import alta, borrar, fijar, sumar

__all__ = [
    "por_id",
    "por_codigo",
    "catalogo",
    "precios",
    "alta",
    "fijar",
    "sumar",
    "borrar",
]
