"""El PIN de 4 dígitos que autoriza pasar el cupo."""
import hashlib


def _ficha(fila):
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return fila
    try:
        return dict(fila)
    except Exception:
        return {}


def quien_autoriza(texto):
    """Devuelve el usuario admin si esos 4 dígitos son su PIN. Si no, vacío."""
    digitos = "".join(c for c in str(texto or "") if c.isdigit())
    if len(digitos) != 4:
        return ""
    from src.base_de_datos.database import db_manager

    try:
        filas = db_manager.execute_query(
            "SELECT username, rol, pin FROM usuarios WHERE pin IS NOT NULL AND pin != ''"
        ) or []
    except Exception:
        return ""
    huella = hashlib.sha256(digitos.encode()).hexdigest()
    for fila in filas:
        ficha = _ficha(fila)
        if str(ficha.get("rol") or "").strip().lower() != "admin":
            continue
        guardado = str(ficha.get("pin") or "").strip()
        if not guardado:
            continue
        if digitos == guardado or huella == guardado:
            return str(ficha.get("username") or "Admin").strip() or "Admin"
    return ""
