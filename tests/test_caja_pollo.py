"""Reglas del pedido automático de pollo por bulto o por corte."""

from src.proveedor_global.frontend.formula.motores import caja_pollo


def _consultar(monkeypatch, stocks):
    monkeypatch.setattr(caja_pollo, "_composicion", lambda _db: [
        ("Suprema", 5), ("Pata Muslo", 8), ("Alitas", 2),
    ])
    monkeypatch.setattr(caja_pollo, "_stocks", lambda _db: stocks)
    monkeypatch.setattr(caja_pollo, "_merma", lambda _db: 0)
    monkeypatch.setattr(caja_pollo, "_costo_kg", lambda _db: 1000)
    return caja_pollo.consultar(None)


def test_pollo_parejo_en_tres_cajas_pide_dos_bultos(monkeypatch):
    dato = _consultar(monkeypatch, {"SUPREMA": 15, "PATA MUSLO": 24})

    assert dato["modo"] == "caja"
    assert dato["pedir"] == 2


def test_pollo_parejo_arriba_de_tres_cajas_no_pide(monkeypatch):
    dato = _consultar(monkeypatch, {"SUPREMA": 20, "PATA MUSLO": 32})

    assert dato["modo"] == "nada"
    assert dato["pedir"] == 0


def test_pollo_con_tres_cajas_de_diferencia_recompone_el_corte_menor_a_seis(monkeypatch):
    dato = _consultar(monkeypatch, {"SUPREMA": 0, "PATA MUSLO": 24})

    assert dato["modo"] == "corte"
    assert dato["nombre"] == "Suprema"
    assert dato["unidad"] == "kg"
    assert dato["pedir"] == 30
    assert dato["max_kg"] == 30


def test_sin_pata_y_con_dos_cajas_de_suprema_pide_cuatro_y_completa_a_seis(monkeypatch):
    dato = _consultar(monkeypatch, {"SUPREMA": 10, "PATA MUSLO": 0})

    assert dato["modo"] == "refuerzo"
    assert dato["pedir"] == 4
    assert dato["extra_nombre"] == "Pata Muslo"
    assert dato["extra_kg"] == 16


def test_pollo_con_diferencia_invertida_recompone_pata_muslo_a_seis(monkeypatch):
    dato = _consultar(monkeypatch, {"SUPREMA": 15, "PATA MUSLO": 0})

    assert dato["modo"] == "corte"
    assert dato["nombre"] == "Pata Muslo"
    assert dato["pedir"] == 48
