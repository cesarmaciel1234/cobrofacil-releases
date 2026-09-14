"""Smoke de cartelería: motores + API del preview. No abre GUI."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

ROOT_OK = True


def _check(nombre, ok, detalle=""):
    global ROOT_OK
    marca = "OK" if ok else "FAIL"
    if not ok:
        ROOT_OK = False
    extra = f"  {detalle}" if detalle else ""
    print(f"  [{marca}] {nombre}{extra}")


def test_estado_tv():
    from src.carteleria.motor_carteleria.estado_tv import (
        armar_rotacion_destacados,
        es_oferta,
        precio_vigente,
    )

    catalogo = [
        {"nombre": "Asado", "precio": 18900, "precio_oferta": 0, "departamento": "CARNE"},
        {
            "nombre": "Oferta De Vacio",
            "precio": 21900,
            "precio_oferta": 19900,
            "cant_oferta": 2,
            "unidad": "KG",
            "departamento": "CARNE",
        },
    ]
    vacio = catalogo[1]
    _check("oferta detectada", es_oferta(vacio))
    _check("precio vigente oferta", precio_vigente(vacio) == 19900)
    _check("precio vigente lista", precio_vigente(catalogo[0]) == 18900)

    paneles = armar_rotacion_destacados(catalogo)
    _check("rotacion es lista", isinstance(paneles, list))
    inventados = [p for p in paneles if p.get("subtitulo") == "Al azar"]
    _check("sin ranking al azar", not inventados, f"{len(paneles)} paneles")


def test_api_preview():
    url = "http://127.0.0.1:8766/api/state"
    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        print(f"  [SKIP] API preview (servidor no levantado)  {exc}")
        return

    precios = data.get("precios") or []
    rotacion = data.get("rotacion") or []
    col3 = data.get("columna3") or []
    _check("API /api/state", True, f"{len(precios)} precios")
    _check("hay precios", len(precios) > 0)
    _check(
        "TV1 ranking",
        any((p.get("items") or []) for p in rotacion),
        ",".join(p.get("id") or "?" for p in rotacion) or "vacio",
    )
    tipos = {s.get("tipo") for s in col3}
    _check("TV3 cruzada+oferta", "cruzada" in tipos and "oferta" in tipos, str(sorted(tipos)))
    _check("tema temu", (data.get("config") or {}).get("carteleria_theme") == "temu")


def main():
    print("Smoke cartelería")
    test_estado_tv()
    test_api_preview()
    print("RESULTADO", "OK" if ROOT_OK else "FAIL")
    return 0 if ROOT_OK else 1


if __name__ == "__main__":
    sys.exit(main())
