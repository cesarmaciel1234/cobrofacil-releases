def _titulo(texto):
    partes = []
    for pieza in str(texto or "").split():
        if pieza.isupper() or pieza.islower():
            partes.append(pieza[:1].upper() + pieza[1:].lower())
        else:
            partes.append(pieza)
    return " ".join(partes)


def _es_express(nombre):
    limpio = " ".join(str(nombre or "").split())
    resto = limpio[8:].replace(" ", "")
    return limpio.lower().startswith("express ") and resto.isdigit()


class SubmotorNombre:
    """Arma el saludo. Si el nombre no está, devuelve el contenedor «Sin datos»."""

    def leer(self, ficha):
        try:
            datos = ficha if isinstance(ficha, dict) else {}
            nombre = " ".join(str(datos.get("nombre") or "").split())
            apellido = " ".join(str(datos.get("apellido") or "").split())
            if _es_express(nombre):
                nombre = ""
            completo = " ".join(parte for parte in (nombre, apellido) if parte)
            if not completo:
                return "Sin datos"
            return "Hola, " + _titulo(completo)
        except Exception:
            return "Sin datos"
