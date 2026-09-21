"""SQL de vitrina: mismos campos que el panel PNG (icono + id)."""

PRECIOS_SELECT = (
    "SELECT categoria, nombre, precio, precio_oferta, precio_oferta_relampago, "
    "precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock, unidad, "
    "es_pesable, departamento, icono, id FROM productos WHERE precio > 0 "
    "AND LOWER(nombre) NOT LIKE '%articulo comun%' "
    "AND LOWER(nombre) NOT LIKE '%venta libre%' "
    "ORDER BY categoria"
)


def sql_sos(rand_func: str) -> str:
    return (
        f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, "
        f"cant_oferta, tipo_unidad_oferta, stock FROM productos "
        f"WHERE precio_oferta_relampago > 0 AND (precio > 0 OR precio_oferta > 0 OR precio_oferta_relampago > 0) "
        f"AND LOWER(nombre) NOT LIKE '%articulo comun%' "
        f"AND LOWER(nombre) NOT LIKE '%venta libre%' "
        f"ORDER BY {rand_func} LIMIT 10"
    )


def sql_top_fallback(rand_func: str) -> str:
    return (
        f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, "
        f"cant_oferta, tipo_unidad_oferta, stock, es_pesable FROM productos WHERE precio > 0 "
        f"AND LOWER(nombre) NOT LIKE '%articulo comun%' "
        f"AND LOWER(nombre) NOT LIKE '%venta libre%' "
        f"ORDER BY {rand_func} LIMIT 10"
    )
