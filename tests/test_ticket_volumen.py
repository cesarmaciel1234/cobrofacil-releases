"""El desglose impreso cabe en el papel configurado."""

from src.historial_ventas.ticket_volumen import (
    armar_ticket_volumen,
    columnas_configuradas,
    lineas_volumen,
    periodo_mes,
)


def test_58_mm_son_32_columnas(monkeypatch):
    from src.config import config

    monkeypatch.setattr(config, "_load_config", lambda: None)
    monkeypatch.setattr(
        config,
        "get",
        lambda key, default=None: 58 if key == "printer_paper_width_mm" else default,
    )
    assert columnas_configuradas() == 32


def test_80_mm_son_48_columnas(monkeypatch):
    from src.config import config

    monkeypatch.setattr(config, "_load_config", lambda: None)
    monkeypatch.setattr(
        config,
        "get",
        lambda key, default=None: 80 if key == "printer_paper_width_mm" else default,
    )
    assert columnas_configuradas() == 48


def test_el_ticket_no_se_pasa_de_58():
    nombre = "OFERTA Pata Y Muslo de novillo en oferta de góndola muy larga"
    filas = [
        {"nombre_producto": nombre, "total_cant": 6.21, "total_monto": 27900, "es_pesable": 1},
        {"nombre_producto": "patitas congelados", "total_cant": 4, "total_monto": 18000, "unidad": "UN"},
    ]
    lineas = lineas_volumen(filas, "20/10/2026", 42, 32, empresa="Carniceria")
    assert all(len(linea) <= 32 for linea in lineas)
    assert sum(1 for linea in lineas if linea.strip() == "Carniceria") >= 2
    assert any("VOLUMEN VENDIDO" in linea for linea in lineas)
    assert any("20/10/2026" in linea for linea in lineas)
    assert any("6.21" in linea and "kg" in linea for linea in lineas)
    assert any("4 un x" in linea for linea in lineas)
    assert any(linea.startswith("Kilos") for linea in lineas)
    assert any(linea.startswith("Unidades") for linea in lineas)
    assert any(linea.endswith("2") and linea.startswith("Articulos") for linea in lineas)
    assert any("Clientes: 42" in linea for linea in lineas)
    assert any("TOTAL" in linea for linea in lineas)
    ticket = armar_ticket_volumen(filas, "20/10/2026", 42, columnas=32, empresa="Carniceria")
    assert ticket.startswith(b"\x1b")
    assert ticket.endswith(b"\x1d\x56\x41\x00")
    assert b"\x1b\x21\x30" in ticket
    assert b"\x1b\x45\x01" in ticket
    assert b"\x1b\x21\x01" in ticket


def test_octubre_tiene_31_dias():
    ini, fin, texto = periodo_mes(2026, 10)
    assert ini == "2026-10-01"
    assert fin == "2026-10-31"
    assert texto == "01/10/2026 al 31/10/2026"
