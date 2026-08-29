"""Vista previa de la cara web sin kiosk ni consultas pesadas a la DB."""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("CARTELERIA_PREVIEW", "1")

from src.carteleria.lanzador_tv.cerebro_lanzador_tv import CarteleriaWebHandler, ThreadedHTTPServer
from src.utils.paths import get_base_path, get_resource_path


def _num(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _producto(row):
    if isinstance(row, dict):
        return {
            "id": row.get("id"),
            "nombre": row.get("nombre") or "",
            "precio": _num(row.get("precio")),
            "precio_oferta": _num(row.get("precio_oferta")),
            "precio_oferta_relampago": _num(row.get("precio_oferta_relampago")),
            "cant_oferta": _num(row.get("cant_oferta")),
            "tipo_unidad_oferta": row.get("tipo_unidad_oferta") or "",
            "unidad": row.get("unidad") or "",
            "es_pesable": row.get("es_pesable") or 0,
            "departamento": row.get("departamento") or row.get("categoria") or "",
            "categoria": row.get("categoria") or "",
            "icono": row.get("icono") or "",
            "es_publicidad": False,
        }
    row = list(row) if isinstance(row, (list, tuple)) else []
    return {
        "id": None,
        "departamento": row[0] if len(row) > 0 else "",
        "categoria": row[0] if len(row) > 0 else "",
        "nombre": row[1] if len(row) > 1 else "",
        "precio": _num(row[2] if len(row) > 2 else 0),
        "precio_oferta": _num(row[3] if len(row) > 3 else 0),
        "precio_oferta_relampago": _num(row[4] if len(row) > 4 else 0),
        "cant_oferta": _num(row[6] if len(row) > 6 else 0),
        "es_publicidad": False,
    }


def _titulo_pregunta(nombre):
    texto = str(nombre or "").strip()
    if texto.lower().startswith("oferta "):
        texto = texto[7:].strip()
    return texto.upper() if texto else "ESTO"


def _slides_columna3(productos, ofertas, top):
    try:
        from src.carteleria.motor_carteleria.estado_tv import armar_columna3
        slides = armar_columna3(productos)
        if slides:
            return slides
    except Exception:
        pass
    cruzadas = []
    por_depto = {}
    for item in productos:
        depto = str(item.get("departamento") or item.get("categoria") or "GENERAL")
        por_depto.setdefault(depto, []).append(item)
    for item in (top or productos)[:4]:
        depto = str(item.get("departamento") or item.get("categoria") or "GENERAL")
        mates = [p["nombre"] for p in por_depto.get(depto, []) if p["nombre"] != item["nombre"]][:3]
        if len(mates) < 2:
            continue
        cruzadas.append({
            "tipo": "cruzada",
            "nombre": item["nombre"],
            "pregunta": f"¿LLEVÁS {_titulo_pregunta(item['nombre'])}?",
            "relacionados": [str(n).upper() for n in mates],
        })
    flashes = []
    for item in ofertas[:4]:
        flashes.append({
            "tipo": "oferta",
            "nombre": item["nombre"],
            "precio": item["precio_oferta"] or item["precio"],
            "precio_original": item["precio"],
            "ahorro": max(item["precio"] - (item["precio_oferta"] or 0), 0),
            "cant_oferta": item.get("cant_oferta") or 0.1,
            "tipo_unidad_oferta": item.get("tipo_unidad_oferta") or "",
            "unidad": item.get("unidad") or "",
            "es_pesable": item.get("es_pesable") or 0,
            "departamento": item.get("departamento") or item.get("categoria") or "",
        })
    slides = []
    n = max(len(cruzadas), len(flashes))
    for i in range(n):
        if i < len(cruzadas):
            slides.append(cruzadas[i])
        if i < len(flashes):
            slides.append(flashes[i])
    return slides


class PreviewWindow:
    def __init__(self):
        cache_path = os.path.join(get_base_path(), "carteleria_cache.json")
        data = {}
        try:
            with open(cache_path, "r", encoding="utf-8") as handle:
                data = json.load(handle) or {}
        except (OSError, ValueError):
            data = {}
        productos = [_producto(row) for row in data.get("precios", [])]
        try:
            from src.carteleria.motor_carteleria.iconos_tv import enriquecer_iconos
            enriquecer_iconos(productos)
        except Exception:
            pass
        try:
            from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad
            motor_publicidad.marcar_lista(productos)
        except Exception:
            pass
        ofertas = [p for p in productos if p["precio_oferta"] > 0 and p["precio_oferta"] < p["precio"]]
        self.rows_precios = productos
        top = (ofertas or productos)[:5]
        for i, item in enumerate(top, start=1):
            item["puesto"] = i
            item["detalle"] = "Carta del local"
        try:
            from src.carteleria.motor_carteleria.estado_tv import armar_rotacion_destacados
            rotacion = armar_rotacion_destacados(productos)
        except Exception:
            rotacion = []
        if not rotacion and top:
            rotacion = [{
                "id": "carta",
                "titulo": "Carta del local",
                "subtitulo": "Precios vigentes",
                "items": top,
            }]
        self._state = {
            "config": {
                "business_name": "MACIEL CARNICERIA",
                "phone": "",
                "carteleria_theme": "temu",
                "mensaje_zocalo": "Ofertas sujetas a stock",
                "data_status": "offline",
            },
            "precios": productos,
            "hero": top[0] if top else None,
            "destacados": top,
            "rotacion": rotacion,
            "combos": [
                {
                    "nombre": item["nombre"],
                    "precio": item["precio_oferta"] or item["precio"],
                    "precio_original": item["precio"],
                    "ahorro": max(item["precio"] - item["precio_oferta"], 0) if item["precio_oferta"] else 0,
                    "productos": item["nombre"],
                    "cant_oferta": item.get("cant_oferta") or 2,
                    "tipo_unidad_oferta": item.get("tipo_unidad_oferta") or "",
                    "unidad": item.get("unidad") or "",
                    "origen": "oferta",
                }
                for item in ofertas[:4]
            ],
            "columna3": _slides_columna3(productos, ofertas, top),
            "ia": [
                {"nombre": item["nombre"], "precio": item["precio_oferta"] or item["precio"], "razon": "Selección del chef"}
                for item in (ofertas or productos)[:4]
            ],
            "climaData": {
                "icono": "sol",
                "temperatura": "22°C",
                "mensaje": "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR",
                "producto_recomendado": "POLLO ENTERO",
                "precio": next(
                    (p["precio"] for p in productos if "pollo entero" in p["nombre"].lower()),
                    4900,
                ),
            },
        }

    def get_web_state(self):
        return self._state


def main():
    web_root = get_resource_path(os.path.join("src", "carteleria", "lanzador_tv", "la_cara_web"))
    window = PreviewWindow()
    handler = lambda *args, **kwargs: CarteleriaWebHandler(
        *args, web_root=web_root, main_window=window, **kwargs
    )
    httpd = ThreadedHTTPServer(("127.0.0.1", 8766), handler)
    print(f"PREVIEW http://127.0.0.1:{httpd.server_address[1]}/", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
