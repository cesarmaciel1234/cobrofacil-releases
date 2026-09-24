import json
import os
from datetime import datetime

RUTA = os.path.join("reportes", "mp_vinculos.json")


def _leer():
    if not os.path.exists(RUTA):
        return {}
    try:
        with open(RUTA, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return datos if isinstance(datos, dict) else {}
    except Exception:
        return {}


def _guardar(datos):
    os.makedirs(os.path.dirname(RUTA), exist_ok=True)
    with open(RUTA, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def asociado(payment_id):
    """El vínculo de ese id, o None si todavía no se usó en un ticket."""
    clave = str(payment_id or "").strip()
    if not clave:
        return None
    for mes in _leer().values():
        if isinstance(mes, dict) and clave in mes:
            return mes[clave]
    return None


def asociar(payment_id, monto, ticket):
    """Guarda el id del mes junto al ticket. No pisa un vínculo que ya existe."""
    clave = str(payment_id or "").strip()
    if not clave or asociado(clave):
        return False
    datos = _leer()
    mes = datetime.now().strftime("%Y-%m")
    libro = datos.get(mes)
    if not isinstance(libro, dict):
        libro = {}
    libro[clave] = {
        "monto": float(monto or 0),
        "ticket": str(ticket),
        "cuando": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    datos[mes] = libro
    _guardar(datos)
    return True
