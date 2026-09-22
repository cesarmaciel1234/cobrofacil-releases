from src.motor_inventario.unidad_medida.logica.normalizar import normalizar_unidad

# Palabras en el nombre de departamento → unidad default del rubro.
_RUBRO_UNIDAD = (
    (("carni", "pollo", "pescado", "verdul", "fiambr", "fiambre", "asado", "carbon"), "kilo"),
    (("tela", "textil", "ropa", "confecc", "mercer"), "metro"),
    (("bebida", "bar", "vino", "licor", "jugo"), "litro"),
    (("panad", "pan ", "factur"), "unidad"),
    (("limpie", "almacen", "kiosco", "bazar"), "unidad"),
)


def unidad_por_departamento(departamento) -> str:
    nom = str(departamento or "").lower()
    if not nom:
        return ""
    directo = normalizar_unidad(nom)
    if directo in ("kilo", "litro", "metro", "unidad", "pack", "gramo", "docena"):
        return directo
    for claves, unidad in _RUBRO_UNIDAD:
        if any(k in nom for k in claves):
            return unidad
    return ""
