from src.base_de_datos.database import db_manager
from src.cajero.paso6_cobro.motor_pagos.comandos.armar_venta import armar_resultado_venta
from src.utils.dinero import redondear_dinero, redondear_items_carrito


def persistir_cobro(datos):
    """Una transaccion: venta + stock. Si es fiado, tambien deuda y CC."""
    resultado = armar_resultado_venta(datos)
    items = redondear_items_carrito(datos.get("items_carrito") or [])
    metodo = datos.get("metodo") or ""
    fiado = None
    if metodo in ("Fiado", "Clientes"):
        fiado = {
            "cliente_id": datos.get("cliente_id"),
            "total": redondear_dinero(resultado.get("total")),
        }
        resultado["cliente_id"] = datos.get("cliente_id")
    try:
        id_v = db_manager.guardar_venta_completa(resultado, items, fiado=fiado)
    except Exception as e:
        from src.base_de_datos.repos.stock_descuento import SinStock
        if isinstance(e, SinStock):
            return None, {"error": str(e)}
        raise
    return id_v, resultado
