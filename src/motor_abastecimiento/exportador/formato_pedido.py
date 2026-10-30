from datetime import datetime

def generar_texto_whatsapp(pedido_proveedor, nombre_comercio="Mi Comercio"):
    """
    Texto corto para el proveedor: qué se pide y cuánto.
    """
    prov_nombre = str(pedido_proveedor.get("proveedor") or "").strip()
    items = pedido_proveedor.get("items", [])
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    codigo = str(pedido_proveedor.get("codigo") or "").strip()
    if codigo.upper() == "EN CASA":
        codigo = ""
    general = bool(pedido_proveedor.get("general"))

    lineas = [
        "--- PEDIDO DE REPOSICION ---",
        f"*Comercio:* {nombre_comercio}",
    ]
    if not general and prov_nombre and prov_nombre.upper() != "SIN PROVEEDOR ASIGNADO":
        lineas.append(f"*Proveedor:* {prov_nombre}")
    if not general and codigo:
        lineas.append(f"*Codigo:* {codigo}")
    lineas.extend([
        f"*Fecha:* {fecha_hoy}",
        "------------------------------------",
    ])

    pedir = [it for it in items if float(it.get("cantidad_a_pedir") or 0) > 0]
    for it in pedir:
        bruto = float(it["cantidad_a_pedir"])
        cant = str(it.get("rango") or (int(bruto) if bruto.is_integer() else f"{bruto:g}"))
        lineas.append(f"- *{cant}x* {it['nombre']}")

    lineas.append("------------------------------------")
    lineas.append("Favor confirmar recepcion y fecha estimada de entrega. ¡Muchas gracias!")

    return "\n".join(lineas)


def mensaje_general(pedidos, nombre_comercio="Mi Comercio"):
    """Un solo texto para Todos: los artículos, sin ficha ni código interno."""
    items = []
    for info in (pedidos or {}).values():
        items.extend(info.get("items") or [])
    return generar_texto_whatsapp(
        {"general": True, "items": items},
        nombre_comercio,
    )


def generar_resumen_general(pedidos_agrupados):
    """
    Genera un resumen global para la pantalla de control del dueño/encargado.
    """
    total_proveedores = sum(
        1 for p in pedidos_agrupados.values()
        if str(p.get("proveedor") or "").strip().upper() != "SIN PROVEEDOR ASIGNADO"
    )
    total_articulos = sum(p["total_items"] for p in pedidos_agrupados.values())
    total_inversion_estimada = round(
        sum(p.get("presupuesto_estimado", p.get("costo_total_estimado", 0.0)) for p in pedidos_agrupados.values()),
        2,
    )

    return {
        "proveedores_involucrados": total_proveedores,
        "total_articulos_faltantes": total_articulos,
        "inversion_total_estimada": total_inversion_estimada,
        "pedidos": pedidos_agrupados
    }
