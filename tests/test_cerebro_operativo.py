from datetime import date

from src.cerebro_global.operacion import evaluar


def test_el_cerebro_toma_la_cantidad_mayor_y_no_suma_dos_senales():
    panorama = evaluar(
        {"pollo": {"pedir": 3, "stock": 2, "prepara": date(2026, 10, 30), "porque": "Pronóstico."}},
        {"pedidos": {"Proveedor": {"items": [{
            "id": "formula:Pollo", "nombre": "Pollo entero (cajas)",
            "es_formula": True, "cantidad_a_pedir": 2, "stock_actual": 2,
        }]}}},
        date(2026, 10, 30),
    )

    assert panorama["modo"] == "borrador"
    assert panorama["total"] == 1
    accion = panorama["acciones"][0]
    assert accion["formula"] == "Pollo"
    assert accion["cantidad"] == 3
    assert accion["fuentes"] == ["predictiva", "abastecimiento"]
    assert accion["estado"] == "preparar_hoy"
    assert accion["requiere_revision"] is True


def test_el_corte_en_kilos_no_se_mezcla_con_el_bulto_en_cajas():
    panorama = evaluar(
        {},
        {"pedidos": {"Proveedor": {"items": [{
            "id": "formula:Pollo:Suprema", "nombre": "Suprema (kg)",
            "es_formula": True, "cantidad_a_pedir": 30, "stock_actual": 0,
        }]}}},
    )

    accion = panorama["acciones"][0]
    assert accion["formula"] == "Pollo"
    assert accion["unidad"] == "kg"
    assert accion["cantidad"] == 30
    assert accion["estado"] == "crítico"
