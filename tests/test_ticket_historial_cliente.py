"""Pruebas del formato ESC/POS de imprimir_historial_cuenta (58 mm y 80 mm)."""

from src.config import config
from src.hardware.printer import printer_manager, resumen_corte_cuenta


def _extraer_texto(raw: bytes) -> str:
    out = bytearray()
    i = 0
    while i < len(raw):
        b = raw[i]
        if b == 0x1B:
            i += 2 if i + 1 < len(raw) and raw[i + 1] == 0x40 else 3
        elif b == 0x1D:
            i += 3 if i + 1 < len(raw) and raw[i + 1] == 0x56 else 2
        else:
            out.append(b)
            i += 1
    return out.decode("cp850", errors="replace")


def _render(monkeypatch, ancho_mm: int, solo_deuda_actual: bool = False):
    capturado = []
    monkeypatch.setattr(config, "_load_config", lambda: None)
    monkeypatch.setattr(
        config,
        "get",
        lambda key, default=None: ancho_mm if key == "printer_paper_width_mm" else default,
    )
    monkeypatch.setattr(printer_manager, "header_dir", "Av. San Martin 450")
    monkeypatch.setattr(printer_manager, "header_tel", "261-444-5566")
    monkeypatch.setattr(
        printer_manager,
        "_send_raw_data",
        lambda data, **_k: capturado.append(data) or True,
    )
    cliente = {
        "nombre": "ruben",
        "dni": "",
        "limite_credito": 400000.0,
        "deuda_actual": 290235.0,
    }
    movs = [
        {
            "fecha": "2026-11-08 11:19:26",
            "tipo": "CARGO",
            "etiqueta": "VENTA",
            "monto": 84728.0,
            "saldo_resultante": 290235.0,
            "referencia": "#1092895",
            "venta_id": 1092895,
            "descripcion": "Venta a cr\ufffddito Ticket #1092895 (excepci\ufffdn admin)",
            "dias": 4,
            "interes_acumulado": 338.91,
        },
        {
            "fecha": "2026-10-29 18:17:02",
            "tipo": "ABONO",
            "etiqueta": "COBRO",
            "monto": 219035.50,
            "saldo_resultante": 0.0,
            "referencia": "COB-348",
            "descripcion": "Cajero CAJERO (Tarjeta: 185696146387)",
        },
        {
            "fecha": "2026-10-13 11:08:00",
            "tipo": "CARGO",
            "etiqueta": "CARGO MANUAL",
            "monto": 32970.0,
            "saldo_resultante": 32970.0,
            "descripcion": "Cargo manual desde cartera",
            "dias": 30,
            "interes_acumulado": 100.0,
        },
    ]
    totales = {
        "ventas": 84728.0,
        "manuales": 32970.0,
        "cargos": 117698.0,
        "abonos": 219035.50,
    }
    assert printer_manager.imprimir_historial_cuenta(
        cliente, movs, totales, solo_deuda_actual=solo_deuda_actual
    )
    return _extraer_texto(capturado[0])


def test_ticket_historial_58mm_espaciado_y_totales(monkeypatch):
    txt = _render(monkeypatch, 58)
    lineas = txt.splitlines()
    assert max(len(l) for l in lineas) <= 32
    assert "Av. San Martin 450" in lineas
    assert "Tel: 261-444-5566" in lineas
    assert "DOCUMENTO NO FISCAL" in lineas
    assert "Periodo: 13/10/26 al 08/11/26" in lineas
    assert "DNI:" not in txt
    assert "?" not in txt
    assert "Disponible           $109,765.00" in lineas
    assert "08/11 11:19  #1092895" in lineas
    assert "ESTADO DE CUENTA" in lineas
    assert "HISTORIAL SALDADO (2)" in lineas
    assert "DEUDA ACTUAL (1)" in lineas
    assert "  VENTA              +$84,728.00" in lineas
    assert "Excepcion admin" not in txt
    assert "  Saldo" not in txt
    assert "  Mant (" not in txt
    assert "------- Cuenta en $0.00 --------" in lineas
    assert "  COBRO             -$219,035.50" in lineas
    assert "  Tarjeta: 185696146387" in lineas
    assert "13/10 11:08  Cargo a mano" in lineas
    # Orden cronológico: fecha más vieja arriba -> más nueva abajo
    idx_vieja = lineas.index("13/10 11:08  Cargo a mano")
    idx_cobro = lineas.index("29/10 18:17  COB-348")
    idx_corte = lineas.index("------- Cuenta en $0.00 --------")
    idx_deuda = lineas.index("DEUDA ACTUAL (1)")
    idx_nueva = lineas.index("08/11 11:19  #1092895")
    assert idx_vieja < idx_cobro < idx_corte < idx_deuda < idx_nueva
    assert "RESUMEN DE CUENTA" in lineas
    assert "Ventas (1)            $84,728.00" in lineas
    assert "Cargos a mano (1)     $32,970.00" in lineas
    assert "Cobros (1)          -$219,035.50" in lineas
    assert txt.count("Mantenimiento") == 1
    assert txt.count("TOTAL ESTIMADO") == 1
    assert "Mantenimiento           +$438.91" in lineas
    assert "TOTAL ESTIMADO       $290,673.91" in lineas
    assert "* Valido al " in txt
    # Separación en blanco entre movimientos
    idx = lineas.index("  CARGO              +$32,970.00")
    assert lineas[idx + 1] == ""


def test_ticket_solo_deuda_actual_omite_saldados(monkeypatch):
    txt = _render(monkeypatch, 58, solo_deuda_actual=True)
    lineas = txt.splitlines()
    assert max(len(l) for l in lineas) <= 32
    assert "DOCUMENTO NO FISCAL" in lineas
    assert "Periodo: 08/11/26" in lineas
    assert "DEUDA ACTUAL (1)" in lineas
    assert "HISTORIAL SALDADO" not in txt
    assert "13/10 11:08" not in txt
    assert "COB-348" not in txt
    assert txt.count("Saldo ant. (29/10)         $0.00") == 1
    assert "08/11 11:19  #1092895" in lineas
    assert "RESUMEN DEL PERIODO" in lineas
    assert "Cargos periodo (1)    $84,728.00" in lineas
    assert "TOTAL ESTIMADO       $290,673.91" in lineas
    assert "* Valido al " in txt


def test_resumen_corte_cuenta_detecta_ultimo_cero():
    movs = [
        {"fecha": "2026-11-08 11:19:26", "tipo": "CARGO", "monto": 50000.0, "saldo_resultante": 50000.0},
        {"fecha": "2026-10-29 18:17:02", "tipo": "ABONO", "etiqueta": "COBRO", "monto": 20000.0, "saldo_resultante": 0.0},
        {"fecha": "2026-10-13 11:08:00", "tipo": "CARGO", "monto": 20000.0, "saldo_resultante": 20000.0},
    ]
    info = resumen_corte_cuenta(movs, 50000.0)
    assert info["tiene_corte"] is True
    assert info["cant_actual"] == 1
    assert info["cant_total"] == 3


def test_ticket_historial_80mm_ancho(monkeypatch):
    txt = _render(monkeypatch, 80)
    lineas = txt.splitlines()
    assert max(len(l) for l in lineas) <= 48
    assert "08/11 11:19  #1092895" in lineas
    assert "  VENTA                              +$84,728.00" in lineas
