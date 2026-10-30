"""Revisa la receta antes de guardarla. No escribe la base."""


def numero(valor):
    """Un peso. Vacío es 0. Un texto que no es número es None."""
    texto = str(valor or "").strip().replace(" ", "")
    if not texto:
        return 0.0
    if "," in texto and "." in texto:
        texto = texto.replace(",", "")
    else:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def revisar(filas, kilos_bulto) -> str:
    """Vacío si el bulto y cada corte se pueden guardar. Si no, el motivo."""
    bulto = numero(kilos_bulto)
    if bulto is None:
        return "Los kilos del bulto no son un número."
    if bulto <= 0:
        return "Cargá los kilos del bulto. De ahí sale el peso de cada corte."
    vistos = set()
    suma = 0.0
    cantidad = 0
    for fila in filas or []:
        if not isinstance(fila, (list, tuple)) or not fila:
            continue
        nombre = str(fila[0] or "").strip()
        kilos = numero(fila[1] if len(fila) > 1 else "")
        if not nombre and (kilos is None or kilos <= 0):
            continue
        if kilos is None:
            return f"{nombre or 'Un corte'} tiene un peso que no es un número."
        if not nombre:
            return "Hay kilos sin nombre de corte."
        clave = nombre.upper()
        if clave in vistos:
            return f"{nombre} está repetido."
        vistos.add(clave)
        if kilos <= 0:
            return f"{nombre} no tiene kilos."
        suma += kilos
        cantidad += 1
    if cantidad == 0:
        return "No hay cortes para guardar."
    if suma - bulto > 0.001:
        return f"Los cortes suman {suma:.2f} kg y el bulto es {bulto:.2f} kg."
    return ""
