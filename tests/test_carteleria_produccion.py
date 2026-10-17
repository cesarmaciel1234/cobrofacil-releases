"""Prueba de cartelería a escala de producción (miles de SKU, HTTP concurrente)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

N = 4000
HTTP_WORKERS = 24
HTTP_CADA = 15


def _catalogo(n=N):
    deptos = ["CARNES", "AVES", "CERDO", "ALMACEN", "EMBUTIDOS"]
    nombres_reales = ["Asado", "Vacío", "Cuadrada", "Hamburguesa", "Picada comun", "Tapa de asado"]
    out = []
    for i in range(n):
        oferta = 9000 + (i % 50) * 10 if i % 17 == 0 else 0
        precio = 12000 + (i % 80) * 100
        nombre = nombres_reales[i % len(nombres_reales)] if i < 200 else f"Corte {i}"
        out.append({
            "id": i + 1,
            "nombre": nombre if i < 200 else f"{nombre}",
            "precio": precio,
            "precio_oferta": oferta if oferta < precio else 0,
            "departamento": deptos[i % len(deptos)],
            "categoria": deptos[i % len(deptos)],
            "stock": 10 + (i % 40),
            "unidad": "KG",
            "es_pesable": 1,
            "icono": "",
        })
    return out


class TestProduccionMasiva(unittest.TestCase):
    def test_normaliza_4000(self):
        from src.carteleria.lanzador_tv.directo.catalogo.aplicar import CatalogoMixin

        t0 = time.perf_counter()
        filas = CatalogoMixin()._normalizar_productos(_catalogo())
        ms = (time.perf_counter() - t0) * 1000
        self.assertEqual(len(filas), N)
        self.assertLess(ms, 800, f"normalizar {N} tardó {ms:.0f} ms")

    def test_tope_json_tv(self):
        from src.carteleria.lanzador_tv.directo.estado.publicar import MAX_PRECIOS_TV, precios_para_tv

        tv = precios_para_tv(_catalogo())
        self.assertEqual(len(tv), MAX_PRECIOS_TV)
        self.assertTrue(any((p.get("precio_oferta") or 0) > 0 for p in tv[:40]))
        blob = json.dumps({"precios": tv}, ensure_ascii=False)
        self.assertLess(len(blob), 250_000, f"JSON TV {len(blob)} bytes")

    def test_cache_atomica_grande(self):
        from src.carteleria.vitrina.red import cache as c

        tmp = tempfile.TemporaryDirectory()
        path = os.path.join(tmp.name, "carteleria_cache.json")
        data = {"precios": _catalogo()}
        with patch.object(c, "cache_path", lambda: path):
            t0 = time.perf_counter()
            c.guardar_cache(data)
            leido = c.leer_cache()
            ms = (time.perf_counter() - t0) * 1000
            c.guardar_cache({"precios": []})
            sigue = c.leer_cache()
        tmp.cleanup()
        self.assertEqual(len(leido["precios"]), N)
        self.assertEqual(len(sigue["precios"]), N)
        self.assertLess(ms, 2500, f"cache {N} tardó {ms:.0f} ms")

    def test_pulso_db_caida_usa_cache(self):
        from src.carteleria.vitrina import pulso as p
        from src.carteleria.vitrina.red import cache as c

        tmp = tempfile.TemporaryDirectory()
        path = os.path.join(tmp.name, "carteleria_cache.json")
        bueno = {"precios": _catalogo(80)}
        with patch.object(c, "cache_path", lambda: path):
            c.guardar_cache(bueno)
            with patch.object(p, "contexto_sync", side_effect=RuntimeError("MariaDB caído")):
                data, status = p.pulso_vitrina()
        tmp.cleanup()
        self.assertEqual(status, "offline")
        self.assertEqual(len(data.get("precios") or []), 80)

    def test_paneles_y_iconos(self):
        from src.carteleria.motor_carteleria.estado_tv import armar_paneles
        from src.carteleria.motor_carteleria import iconos_tv

        iconos_tv._png_nombre_cache.clear()
        iconos_tv._png_indice_cache = None
        cat = _catalogo(800)
        with patch("src.carteleria.motor_carteleria.iconos_tv._mapa_iconos_db", lambda: {}):
            t0 = time.perf_counter()
            paneles = armar_paneles(cat, "sol", "", ranking_remoto={})
            ms1 = (time.perf_counter() - t0) * 1000
            t0 = time.perf_counter()
            paneles2 = armar_paneles(cat, "sol", "", ranking_remoto={})
            ms2 = (time.perf_counter() - t0) * 1000
        self.assertTrue(paneles.get("rotacion") or paneles.get("destacados"))
        self.assertTrue(paneles2.get("rotacion") or paneles2.get("destacados"))
        self.assertLess(ms1, 12000, f"primer armar_paneles 800 tardó {ms1:.0f} ms")
        self.assertLess(ms2, 4000, f"segundo armar_paneles 800 tardó {ms2:.0f} ms")

    def test_http_concurrente(self):
        from src.carteleria.lanzador_tv.cerebro_lanzador_tv import (
            CarteleriaWebHandler,
            ThreadedHTTPServer,
            cargar_web_tv,
        )
        from src.carteleria.lanzador_tv.directo.estado.publicar import precios_para_tv

        web_root, zip_store = cargar_web_tv()
        state = {
            "config": {"data_status": "offline", "business_name": "PRUEBA"},
            "precios": precios_para_tv(_catalogo()),
            "rotacion": [{"id": "inventario", "titulo": "Lista", "items": _catalogo(8)}],
            "destacados": _catalogo(4),
        }

        class MW:
            def get_web_state(self):
                return state

        handler = lambda *a, **k: CarteleriaWebHandler(
            *a, web_root=web_root, main_window=MW(), zip_store=zip_store, **k
        )
        httpd = None
        port = None
        for p in range(18765, 18775):
            try:
                httpd = ThreadedHTTPServer(("127.0.0.1", p), handler)
                port = p
                break
            except OSError:
                continue
        self.assertIsNotNone(httpd, "no hay puerto HTTP libre")
        th = threading.Thread(target=httpd.serve_forever, daemon=True)
        th.start()
        url = f"http://127.0.0.1:{port}/api/state"
        html = f"http://127.0.0.1:{port}/"
        try:
            with urllib.request.urlopen(html, timeout=6) as resp:
                body = resp.read()
            self.assertIn(b"html", body.lower()[:200] or body.lower())
            t0 = time.perf_counter()
            errores = []

            def golpe():
                try:
                    with urllib.request.urlopen(url, timeout=6) as r:
                        data = json.loads(r.read().decode("utf-8"))
                    if len(data.get("precios") or []) == 0:
                        errores.append("sin precios")
                except Exception as e:
                    errores.append(str(e))

            with ThreadPoolExecutor(max_workers=HTTP_WORKERS) as pool:
                futs = [pool.submit(golpe) for _ in range(HTTP_WORKERS * HTTP_CADA)]
                for f in as_completed(futs):
                    f.result()
            ms = (time.perf_counter() - t0) * 1000
            self.assertFalse(errores, errores[:5])
            self.assertLess(ms, 8000, f"{HTTP_WORKERS * HTTP_CADA} GET tardaron {ms:.0f} ms")
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
