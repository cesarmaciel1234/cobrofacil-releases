"""Caché y pulso: MariaDB puede faltar; no se pisa un JSON bueno."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestCacheTv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "carteleria_cache.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_guarda_vacio(self):
        from src.carteleria.vitrina.red import cache as c

        with patch.object(c, "cache_path", lambda: self.path):
            c.guardar_cache({"precios": []})
            self.assertFalse(os.path.isfile(self.path))
            c.guardar_cache({"precios": [{"nombre": "Asado", "precio": 1}]})
            self.assertTrue(os.path.isfile(self.path))
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(len(data["precios"]), 1)
            c.guardar_cache({"precios": []})
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(len(data["precios"]), 1)

    def test_leer_inexistente(self):
        from src.carteleria.vitrina.red import cache as c

        with patch.object(c, "cache_path", lambda: self.path):
            self.assertIsNone(c.leer_cache())

    def test_aplicar_no_borra(self):
        from src.carteleria.lanzador_tv.directo.catalogo.aplicar import CatalogoMixin

        class Fake(CatalogoMixin):
            def __init__(self):
                self.rows_precios = [{"nombre": "Asado", "precio": 100}]
                self.publicado = False

            def _publicar_estado(self):
                self.publicado = True

            def _refrescar_paneles(self, force=False):
                raise AssertionError("no debe refrescar con lista vacía si ya hay precios")

        fake = Fake()
        fake._aplicar_catalogo([])
        self.assertEqual(fake.rows_precios[0]["nombre"], "Asado")
        self.assertTrue(fake.publicado)


if __name__ == "__main__":
    unittest.main()
