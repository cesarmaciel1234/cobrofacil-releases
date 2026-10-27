"""F3 pide el día al mismo listado que el historial del jefe."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestHistorialF3(unittest.TestCase):
    def test_el_dia_sale_del_listado(self):
        from src.cajero.paso8_historial.logica.historial_controller import HistorialController

        with patch(
            "src.historial_ventas.listar.listar_tickets",
            return_value=([{"id": 1011491}], 18835.0),
        ) as pedido:
            filas, total = HistorialController().get_ventas(
                txt_search="",
                metodo_filt="TODOS",
                q_date_iso="2026-10-19",
                q_date_l1="19/10/2026",
                q_date_l2="19/10/2026",
                is_default_time=True,
            )
        self.assertEqual(filas[0]["id"], 1011491)
        self.assertEqual(total, 18835.0)
        self.assertEqual(pedido.call_args.kwargs["fecha_iso"], "2026-10-19")
        self.assertFalse(pedido.call_args.kwargs["ver_todo"])


if __name__ == "__main__":
    unittest.main()
