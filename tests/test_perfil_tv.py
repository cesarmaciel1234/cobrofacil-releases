"""Chromium: look premium en cualquier PC."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestPerfilTv(unittest.TestCase):
    def tearDown(self):
        from src.carteleria.lanzador_tv.perfil_pc import limpiar_cache_perfil
        limpiar_cache_perfil()

    def test_bajo_recurso_es_premium(self):
        from src.carteleria.lanzador_tv.perfil_pc import detectar_perfil, perfil_activo, limpiar_cache_perfil

        limpiar_cache_perfil()
        with patch("src.carteleria.lanzador_tv.perfil_pc._ram_gb", return_value=4.0):
            self.assertEqual(detectar_perfil(), "max")
            self.assertEqual(perfil_activo(), "max")

    def test_alta_gama_es_premium(self):
        from src.carteleria.lanzador_tv.perfil_pc import detectar_perfil

        with patch("src.carteleria.lanzador_tv.perfil_pc._ram_gb", return_value=16.0):
            self.assertEqual(detectar_perfil(), "max")

    def test_ticker_mismo_tope(self):
        from src.carteleria.lanzador_tv.directo.estado.publicar import precios_para_tv

        rows = [{"nombre": f"P{i}", "precio": 1000, "precio_oferta": 0} for i in range(400)]
        self.assertEqual(len(precios_para_tv(rows, "eco")), 96)
        self.assertEqual(len(precios_para_tv(rows, "max")), 96)

    def test_flags_gpu(self):
        from src.carteleria.lanzador_tv.perfil_pc import flags_chrome_perfil

        flags = flags_chrome_perfil("eco")
        self.assertIn("--enable-gpu-rasterization", flags)
        self.assertIn("--use-angle=d3d11", flags)
        self.assertIn("--enable-oop-rasterization", flags)
        self.assertIn("--enable-accelerated-2d-canvas", flags)
        self.assertIn("--num-raster-threads=2", flags)
        self.assertNotIn("--enable-zero-copy", flags)
        self.assertFalse(any("Vulkan" in f for f in flags))
        self.assertNotIn("--disable-http-cache", flags)


if __name__ == "__main__":
    unittest.main()
