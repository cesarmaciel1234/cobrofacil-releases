from src.utils.dinero import redondear_dinero


def armar_resultado_venta(datos):
    metodo = datos.get("metodo") or ""
    total_final = redondear_dinero(datos.get("total_final"))
    p1 = redondear_dinero(datos.get("p1"))
    p2 = redondear_dinero(datos.get("p2"))
    es_caja = metodo in ("Efectivo", "Mixto")
    pago_efectivo = p1 if es_caja else 0.0
    pago_otro = p2 if metodo == "Mixto" else (p1 if metodo != "Efectivo" else 0.0)
    overpay = redondear_dinero((p1 + p2) - total_final)
    cambio = redondear_dinero(max(0.0, overpay)) if es_caja else 0.0
    estado = "COMPLETADA"
    nombre = ""
    if datos.get("nombre_pendiente"):
        estado = "TRANSF_PENDIENTE"
        nombre = datos.get("nombre_pendiente") or ""
    return {
        "total": total_final,
        "pago_con": redondear_dinero(p1 + p2),
        "cambio": cambio,
        "pago_efectivo": pago_efectivo,
        "pago_otro": pago_otro,
        "usuario": datos.get("cajero") or "",
        "usuario_secundario": datos.get("cajero_sec") or "",
        "metodo_pago": metodo,
        "estado": estado,
        "cliente_nombre": nombre,
        "descuento": redondear_dinero(
            float(datos.get("descuento") or 0) + float(datos.get("oferta") or 0)
        ),
        "recargo": redondear_dinero(datos.get("recargo")),
        "request_id": datos.get("request_id"),
    }
