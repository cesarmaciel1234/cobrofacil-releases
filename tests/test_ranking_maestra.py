"""La maestra arma lo más vendido aunque el pulso llegue sin ranking."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

RANKING = {
    "hoy_volumen": [{"nombre": "Asado", "cantidad": 4, "recaudacion": 8000}],
    "hoy_frecuencia": [{"nombre": "Asado", "cantidad": 2, "recaudacion": 8000}],
    "ayer_volumen": [],
    "ayer_frecuencia": [],
    "semana_volumen": [],
    "semana_frecuencia": [],
}


class TestRankingMaestra(unittest.TestCase):
    def test_pulso_sin_ranking_pega_ventas_locales(self):
        from src.carteleria.vitrina.aplicar import fusionar_http

        with patch(
            "src.central_red_global.sync_tienda.rol.es_esclava",
            return_value=False,
        ), patch(
            "src.central_red_global.sync_tienda.ranking.motor.ranking_carteleria",
            return_value=RANKING,
        ):
            data = fusionar_http({"precios": [{"nombre": "Asado", "precio": 10000}]}, None, "")
        self.assertEqual(data["ranking"]["hoy_volumen"][0]["nombre"], "Asado")

    def test_ranking_vacio_no_bloquea_ventas(self):
        from src.carteleria.motor_carteleria.estado_tv import armar_paneles

        filas = [{"nombre": "Asado", "cantidad": 4, "recaudacion": 8000}]
        productos = [{
            "id": 1,
            "nombre": "Asado",
            "precio": 10000,
            "precio_oferta": 0,
            "unidad": "KG",
            "es_pesable": 1,
        }]
        with patch(
            "src.carteleria.motor_carteleria.iconos_tv.enriquecer_iconos",
            side_effect=lambda items: items,
        ), patch(
            "src.carteleria.motor_carteleria.motor_publicidad.motor_publicidad.marcar_lista",
            side_effect=lambda items: items,
        ), patch(
            "src.cerebro_global.reporte_ventas_cerebro.motor_ventas.MotorVentas.get_top_ventas",
            return_value=filas,
        ) as top:
            paneles = armar_paneles(productos, ranking_remoto={})
        self.assertTrue(top.called)
        nombres = []
        for bloque in paneles.get("rotacion") or []:
            for item in bloque.get("items") or []:
                nombres.append(item.get("nombre"))
        self.assertIn("Asado", nombres)

    def test_columna3_usa_el_mismo_ticket(self):
        from src.carteleria.motor_carteleria.estado_tv import armar_columna3

        slide = {
            "tipo": "cruzada",
            "nombre": "Asado",
            "pregunta": "¿LLEVÁS ASADO?",
            "relacionados": ["VACIO"],
            "fuente": "tickets",
        }
        with patch(
            "src.carteleria.motor_carteleria.venta_cruzada.VentaCruzadaInteligente.armar_slides",
            return_value=[slide],
        ) as armar, patch(
            "src.carteleria.motor_carteleria.venta_cruzada.VentaCruzadaInteligente.usar_relleno_catalogo",
            return_value=False,
        ):
            out = armar_columna3(
                [{"nombre": "Aceite de oliva", "precio": 3000, "departamento": "ALMACEN"}],
                ranking_remoto={"hoy_volumen": [{"nombre": "Asado", "cantidad": 4, "recaudacion": 1}]},
            )
        self.assertTrue(armar.called)
        self.assertEqual(out[0]["fuente"], "tickets")
        self.assertEqual(out[0]["relacionados"], ["VACIO"])


if __name__ == "__main__":
    unittest.main()
