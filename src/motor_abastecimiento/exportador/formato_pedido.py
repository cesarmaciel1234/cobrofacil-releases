from datetime import datetime

def generar_texto_whatsapp(pedido_proveedor, nombre_comercio="Mi Comercio"):
    """
    Formatea el pedido para un proveedor en texto limpio, profesional y listo
    para ser enviado por WhatsApp o mensaje de texto.
    Usa caracteres compatibles con cualquier consola y teléfono móvil.
    """
    prov_nombre = pedido_proveedor.get("proveedor", "Proveedor")
    items = pedido_proveedor.get("items", [])
    total_costo = pedido_proveedor.get("costo_total_estimado", 0.0)
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")

    lineas = [
        f"--- PEDIDO DE REPOSICION ---",
        f"*Comercio:* {nombre_comercio}",
        f"*Proveedor:* {prov_nombre}",
        *([f"*Codigo:* {pedido_proveedor.get('codigo')}"] if pedido_proveedor.get("codigo") else []),
        f"*Fecha:* {fecha_hoy}",
        "------------------------------------"
    ]

    pedir = [it for it in items if float(it.get("cantidad_a_pedir") or 0) > 0]
    sin_cantidad = [it for it in items if float(it.get("cantidad_a_pedir") or 0) <= 0]
    for it in pedir:
        bruto = float(it["cantidad_a_pedir"])
        cant = int(bruto) if bruto.is_integer() else f"{bruto:g}"
        nom = it["nombre"]
        cod = f" [{it['codigo']}]" if it.get("codigo") else ""
        lineas.append(f"- *{cant}x* {nom}{cod}")
    if sin_cantidad:
        lineas.append("Sin cantidad a pedir:")
        for it in sin_cantidad:
            lineas.append(f"- {it['nombre']}")

    lineas.append("------------------------------------")
    lineas.append(f"*Total articulos pedidos:* {len(pedir)}")
    if total_costo > 0:
        from src.proveedor_global.backend.moneda import texto

        lineas.append(f"*Costo total estimado:* {texto(total_costo)}")
    lineas.append("------------------------------------")
    lineas.append("Favor confirmar recepcion y fecha estimada de entrega. ¡Muchas gracias!")

    return "\n".join(lineas)

def generar_resumen_general(pedidos_agrupados):
    """
    Genera un resumen global para la pantalla de control del dueño/encargado.
    """
    total_proveedores = len(pedidos_agrupados)
    total_articulos = sum(p["total_items"] for p in pedidos_agrupados.values())
    total_inversion_estimada = round(sum(p["costo_total_estimado"] for p in pedidos_agrupados.values()), 2)

    return {
        "proveedores_involucrados": total_proveedores,
        "total_articulos_faltantes": total_articulos,
        "inversion_total_estimada": total_inversion_estimada,
        "pedidos": pedidos_agrupados
    }
