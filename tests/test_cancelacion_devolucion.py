"""Cancelar un ticket: se devuelve en efectivo y el cierre cuadra (sin BD)."""
import pytest

from src.base_de_datos.repos.ventas import calcular_devolucion


def venta(metodo, total, estado="COMPLETADA", caja=1, efectivo=0.0, cambio=0.0):
    return {
        "estado": estado, "caja_id": caja, "usuario": "cajero", "total": total,
        "metodo_pago": metodo, "pago_efectivo": efectivo, "cambio": cambio,
    }


@pytest.mark.parametrize("fila, caja, devolver, retiro, ingreso", [
    # Efectivo del turno abierto: la venta cancelada deja de sumar, no hace falta retiro.
    (venta("Efectivo", 800, efectivo=1000, cambio=200), 1, 800, 0, 0),
    # Digital del turno: la plata quedó en MP, el efectivo sale del cajón.
    (venta("Transferencia", 800), 1, 800, 800, 0),
    (venta("QR", 1250.5), 1, 1250.5, 1250.5, 0),
    (venta("Tarjeta", 3000), 1, 3000, 3000, 0),
    # Mixto: la parte en efectivo sale sola, la digital es retiro.
    (venta("Mixto", 1000, efectivo=400), 1, 1000, 600, 0),
    # Venta de un turno ya cerrado: todo es retiro del turno actual.
    (venta("Efectivo", 800, estado="CERRADA", efectivo=800), 1, 800, 800, 0),
    (venta("Transferencia", 800, estado="CERRADA"), 1, 800, 800, 0),
    # Fiado y clientes: no hay efectivo que devolver, se anula la deuda.
    (venta("Fiado", 5000), 1, 0, 0, 0),
    (venta("Clientes", 5000), 1, 0, 0, 0),
    # Otra caja cancela un efectivo abierto: sale de la caja 2, la caja 1 conserva su efectivo.
    (venta("Efectivo", 800, caja=1, efectivo=800), 2, 800, 800, 800),
])
def test_calcular_devolucion(fila, caja, devolver, retiro, ingreso):
    plan = calcular_devolucion(fila, caja)
    assert plan["a_devolver"] == devolver
    assert plan["retiro"] == retiro
    assert plan["ingreso_origen"] == ingreso


def test_cuadra_el_cajon_en_cada_caso():
    """Esperado antes − (lo que deja de sumar la venta) − retiro + ingreso = esperado − devuelto en la caja que devuelve."""
    casos = [
        (venta("Efectivo", 800, efectivo=1000, cambio=200), 1),
        (venta("Mixto", 1000, efectivo=400), 1),
        (venta("Transferencia", 800), 1),
    ]
    for fila, caja in casos:
        plan = calcular_devolucion(fila, caja)
        deja_de_sumar = max(0.0, float(fila["pago_efectivo"]) - float(fila["cambio"]))
        assert round(deja_de_sumar + plan["retiro"], 2) == plan["a_devolver"]
