from src.base_de_datos.database import db_manager
from src.cajero.paso6_cobro.motor_pagos.comandos.armar_venta import armar_resultado_venta
from src.utils.dinero import redondear_dinero, redondear_items_carrito


def persistir_cobro(datos):
    """Una transaccion: venta + stock. Si es fiado, tambien deuda y CC."""
    resultado = armar_resultado_venta(datos)
    items = redondear_items_carrito(datos.get("items_carrito") or [])
    metodo = datos.get("metodo") or ""
    fiado = None
    parte = redondear_dinero(datos.get("fiado_parcial") or 0)
    if metodo in ("Fiado", "Clientes") or (metodo == "Mixto" and parte > 0.009):
        fiado = {
            "cliente_id": datos.get("cliente_id"),
            "total": parte if metodo == "Mixto" else redondear_dinero(resultado.get("total")),
            "excepcion": datos.get("excepcion") or "",
        }
        resultado["cliente_id"] = datos.get("cliente_id")
    try:
        id_v = db_manager.guardar_venta_completa(resultado, items, fiado=fiado)
    except Exception as e:
        from src.base_de_datos.repos.stock_descuento import SinStock
        from src.base_de_datos.repos.ventas import CreditoInsuficiente
        if isinstance(e, (SinStock, CreditoInsuficiente)):
            return None, {"error": str(e)}
        raise
    # Cupo relámpago: no tumba la venta si falla
    try:
        from src.motor_descuentos.ofertas.motor import MotorOfertas
        MotorOfertas().consumir_relampago_en_items(items)
    except Exception:
        pass
    return id_v, resultado
