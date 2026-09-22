def armar_resultado_venta(datos):
    metodo = datos.get("metodo") or ""
    total_final = float(datos.get("total_final") or 0)
    p1 = float(datos.get("p1") or 0)
    p2 = float(datos.get("p2") or 0)
    es_caja = metodo in ("Efectivo", "Mixto")
    pago_efectivo = p1 if es_caja else 0.0
    pago_otro = p2 if metodo == "Mixto" else (p1 if metodo != "Efectivo" else 0.0)
    overpay = (p1 + p2) - total_final
    cambio = max(0.0, overpay) if es_caja else 0.0
    estado = "COMPLETADA"
    nombre = ""
    if datos.get("nombre_pendiente"):
        estado = "TRANSF_PENDIENTE"
        nombre = datos.get("nombre_pendiente") or ""
    return {
        "total": total_final,
        "pago_con": p1 + p2,
        "cambio": cambio,
        "pago_efectivo": pago_efectivo,
        "pago_otro": pago_otro,
        "usuario": datos.get("cajero") or "",
        "usuario_secundario": datos.get("cajero_sec") or "",
        "metodo_pago": metodo,
        "estado": estado,
        "cliente_nombre": nombre,
        "descuento": float(datos.get("descuento") or 0) + float(datos.get("oferta") or 0),
        "recargo": float(datos.get("recargo") or 0),
        "request_id": datos.get("request_id"),
    }
