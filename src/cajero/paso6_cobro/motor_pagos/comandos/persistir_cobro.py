from src.base_de_datos.database import db_manager
from src.cajero.paso6_cobro.motor_pagos.comandos.armar_venta import armar_resultado_venta


def persistir_cobro(datos):
    """Una transaccion: venta + stock. Si es fiado, tambien deuda y CC."""
    resultado = armar_resultado_venta(datos)
    metodo = datos.get("metodo") or ""
    fiado = None
    if metodo in ("Fiado", "Clientes"):
        fiado = {
            "cliente_id": datos.get("cliente_id"),
            "total": float(datos.get("total_final") or 0),
        }
        resultado["cliente_id"] = datos.get("cliente_id")
    id_v = db_manager.guardar_venta_completa(
        resultado, datos.get("items_carrito") or [], fiado=fiado
    )
    return id_v, resultado
