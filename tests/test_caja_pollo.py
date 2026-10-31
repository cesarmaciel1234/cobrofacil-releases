"""Reglas del pedido automático de pollo por bulto o por corte."""

from datetime import date

from src.proveedor_global.frontend.formula.motores import caja_pollo

_MIERCOLES = date(2026, 10, 28)
_VIERNES = date(2026, 10, 30)
_SABADO = date(2026, 10, 31)
_DOMINGO = date(2026, 11, 1)
_ENERO = date(2027, 1, 10)


def _consultar(monkeypatch, stocks, dia=_MIERCOLES, cortes=None, buena_epoca=None):
    pares = cortes or [("Suprema", 5), ("Pata Muslo", 8), ("Alitas", 2)]
    monkeypatch.setattr(caja_pollo, "_composicion", lambda _db: pares)
    monkeypatch.setattr(caja_pollo, "_stocks", lambda _db: stocks)
    monkeypatch.setattr(caja_pollo, "_merma", lambda _db: 0)
    monkeypatch.setattr(caja_pollo, "_costo_kg", lambda _db: 1000)
    return caja_pollo.consultar(None, dia=dia, buena_epoca=buena_epoca)


def test_tres_cajones_enteros_completan_a_diez(monkeypatch):
    dato = _consultar(monkeypatch, {"SUPREMA": 15, "PATA MUSLO": 24})

    assert dato["modo"] == "caja"
    assert dato["pedir"] == 7
    assert dato["max_kg"] == 10


def test_diez_cajones_enteros_no_pide(monkeypatch):
    dato = _consultar(monkeypatch, {"SUPREMA": 50, "PATA MUSLO": 80})

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


def test_un_cajon_entero_completa_a_diez(monkeypatch):
    dato = _consultar(
        monkeypatch,
        {"SUPREMA": 15, "PATA MUSLO": 20},
        dia=_VIERNES,
        cortes=[("Suprema", 15), ("Pata Muslo", 20), ("Alitas", 2)],
    )

    assert dato["modo"] == "caja"
    assert dato["pedir"] == 9
    assert dato["max_kg"] == 10


def test_stock_de_camara_cuenta_un_cajon_entero(monkeypatch):
    dato = _consultar(
        monkeypatch,
        {"SUPREMA": 20.4, "PATA MUSLO": 46.2},
        dia=_SABADO,
        cortes=[("Suprema", 15), ("Pata Muslo", 20), ("Alitas", 2)],
    )

    assert dato["modo"] == "caja"
    assert dato["pedir"] == 9


def test_domingo_tambien_completa_a_diez(monkeypatch):
    dato = _consultar(
        monkeypatch,
        {"SUPREMA": 15, "PATA MUSLO": 20},
        dia=_DOMINGO,
        cortes=[("Suprema", 15), ("Pata Muslo", 20), ("Alitas", 2)],
    )

    assert dato["modo"] == "caja"
    assert dato["pedir"] == 9
    assert dato["max_kg"] == 10


def test_buena_epoca_completa_a_quince(monkeypatch):
    dato = _consultar(
        monkeypatch,
        {"SUPREMA": 15, "PATA MUSLO": 20},
        dia=_ENERO,
        cortes=[("Suprema", 15), ("Pata Muslo", 20), ("Alitas", 2)],
    )

    assert dato["modo"] == "caja"
    assert dato["pedir"] == 14
    assert dato["max_kg"] == 15
