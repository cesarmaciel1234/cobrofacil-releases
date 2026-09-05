"""Test de estructura de cartelería: carpetas, temas y pack de la cara TV."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CARTELERIA = os.path.join(ROOT, "src", "carteleria")
CARA = os.path.join(CARTELERIA, "lanzador_tv", "la_cara_web")
TEMAS = ("apple", "temu", "premium", "blackfriday")


class TestCarteleriaEstructura(unittest.TestCase):
    def test_modulos_python_vivos(self):
        for rel in (
            "carteleria.py",
            "admin15_carteleria.py",
            "theme.py",
            "dashboard/dashboard_main.py",
            "lanzador_tv/cerebro_lanzador_tv.py",
            "lanzador_tv/lanzador_directo.py",
            "lanzador_tv/tv_cara_pack.py",
            "lanzador_tv/ui_lanzador_tv.py",
            "motor_carteleria/estado_tv.py",
            "motor_carteleria/db_sync_worker.py",
            "creador_png/ventana_html.py",
        ):
            path = os.path.join(CARTELERIA, rel.replace("/", os.sep))
            self.assertTrue(os.path.isfile(path), f"falta {rel}")

    def test_el_cerebro_sin_codigo(self):
        carpeta = os.path.join(CARTELERIA, "el_cerebro")
        if not os.path.isdir(carpeta):
            return
        pys = [n for n in os.listdir(carpeta) if n.endswith(".py")]
        self.assertTrue(set(pys) <= {"__init__.py"}, "el_cerebro solo debe reexportar, sin lógica nueva")

    def test_cara_web_minima(self):
        for rel in (
            "index.html",
            "app.js",
            "css/tokens.css",
            "css/style.css",
            "css/columna4_chef.css",
        ):
            path = os.path.join(CARA, rel.replace("/", os.sep))
            self.assertTrue(os.path.isfile(path), f"falta cara web {rel}")

    def test_temas_completos(self):
        for tema in TEMAS:
            for nombre in ("colores.css", "estilos.css"):
                path = os.path.join(CARA, "css", "themes", tema, nombre)
                self.assertTrue(os.path.isfile(path), f"falta tema {tema}/{nombre}")

    def test_index_carga_tema(self):
        with open(os.path.join(CARA, "index.html"), encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("css/themes/", html)
        self.assertIn("app.js", html)

    def test_pack_blob_tiene_index(self):
        from src.carteleria.lanzador_tv.tv_cara_pack import pack_source, _bytes_desencriptados
        import zipfile
        import io

        dest = os.path.join(tempfile.gettempdir(), "tpv_test_tv_cara.bin")
        pack_source(dest, CARA)
        self.assertGreater(os.path.getsize(dest), 32)
        raw = _bytes_desencriptados(dest)
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            nombres = zf.namelist()
        self.assertIn("index.html", nombres)
        self.assertTrue(any(n.endswith("themes/apple/colores.css") for n in nombres))

    def test_estado_tv_ofertas(self):
        from src.carteleria.motor_carteleria.estado_tv import es_oferta, precio_vigente

        vacio = {"precio": 21900, "precio_oferta": 19900}
        asado = {"precio": 18900, "precio_oferta": 0}
        self.assertTrue(es_oferta(vacio))
        self.assertEqual(precio_vigente(vacio), 19900)
        self.assertEqual(precio_vigente(asado), 18900)


if __name__ == "__main__":
    unittest.main()
