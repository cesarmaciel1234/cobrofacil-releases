import csv
import json

from src.admin.mercadopago.historial import archivo, nodo
from src.cajero.paso6_cobro.vinculo_mp import libro


def _write_csv(path, rows, columns=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(columns or archivo.COLUMNAS)
        writer.writerows(rows)


def _row(payment_id, state="APPROVED", changed="", registered="2026-09-28 10:00:00"):
    return [
        "2026-09-28 09:00:00",
        payment_id,
        "100.00",
        "Cliente",
        "cliente@example.com",
        state,
        registered,
        "regular_payment",
        "95.00",
        "5.00",
        changed,
    ]


def test_historial_mp_se_combina_ida_y_vuelta(tmp_path, monkeypatch):
    csv_local = tmp_path / "local" / "reportes" / "mercado_pago_sync.csv"
    links_local = tmp_path / "local" / "reportes" / "mp_vinculos.json"
    root = tmp_path / "USB" / "CobroFacil_Nodo"
    csv_node = root / "reportes" / "mercado_pago_sync.csv"
    links_node = root / "reportes" / "mp_vinculos.json"
    monkeypatch.setattr(archivo, "RUTA", str(csv_local))
    monkeypatch.setattr(libro, "RUTA", str(links_local))

    _write_csv(csv_local, [_row("101"), _row("103"), _row("105")])
    _write_csv(csv_node, [
        _row("101", "OMITIDO", "2026-09-29 08:30:00.000000"),
        _row("102"),
        _row("104", "OMITIDO"),
        _row("105", "OMITIDO"),
    ])
    links_local.parent.mkdir(parents=True, exist_ok=True)
    links_local.write_text(json.dumps({
        "2026-09": {"101": {"monto": 100, "ticket": "LOCAL-1", "cuando": "2026-09-29 08:00:00"}}
    }), encoding="utf-8")
    links_node.parent.mkdir(parents=True, exist_ok=True)
    links_node.write_text(json.dumps({
        "2026-09": {
            "101": {"monto": 100, "ticket": "NODO-1", "cuando": "2026-09-29 08:10:00"},
            "102": {"monto": 100, "ticket": "NODO-2", "cuando": "2026-09-29 08:05:00"},
        }
    }), encoding="utf-8")

    nodo.sincronizar_nodo(str(root))

    with csv_local.open(encoding="utf-8-sig", newline="") as f:
        local = {row["ID de Pago"]: row for row in csv.DictReader(f)}
    with csv_node.open(encoding="utf-8-sig", newline="") as f:
        portable = {row["ID de Pago"]: row for row in csv.DictReader(f)}
    assert set(local) == {"101", "102", "103", "104", "105"}
    assert local == portable
    assert local["101"]["Estado"] == "OMITIDO"
    assert local["104"]["Estado"] == "OMITIDO"
    assert local["105"]["Estado"] == "OMITIDO"

    local_links = json.loads(links_local.read_text(encoding="utf-8"))
    portable_links = json.loads(links_node.read_text(encoding="utf-8"))
    assert local_links == portable_links
    assert local_links["2026-09"]["101"]["ticket"] == "LOCAL-1"
    assert local_links["2026-09"]["102"]["ticket"] == "NODO-2"


def test_omitir_y_actualizar_api_preserva_estado_y_marca(tmp_path, monkeypatch):
    monkeypatch.setattr(archivo, "RUTA", str(tmp_path / "reportes" / "mercado_pago_sync.csv"))
    pago = {
        "id": "pago-1",
        "transaction_amount": 100,
        "date_approved": "2026-09-29T09:00:00-03:00",
        "status": "approved",
        "payer": {"email": "cliente@example.com", "first_name": "Ana"},
        "transaction_details": {"net_received_amount": 95},
    }

    assert archivo.guardar([pago]) == 1
    assert archivo.omitir("pago-1")
    with open(archivo.RUTA, encoding="utf-8-sig", newline="") as f:
        fila_omitida = next(csv.DictReader(f))
    marca = fila_omitida[archivo.COLUMNA_CAMBIO_ESTADO]
    assert fila_omitida["Estado"] == "OMITIDO"

    assert archivo.guardar([pago]) == 0
    with open(archivo.RUTA, encoding="utf-8-sig", newline="") as f:
        fila_actualizada = next(csv.DictReader(f))
    assert fila_actualizada["Estado"] == "OMITIDO"
    assert fila_actualizada[archivo.COLUMNA_CAMBIO_ESTADO] == marca

    assert archivo.omitir("pago-1")
    with open(archivo.RUTA, encoding="utf-8-sig", newline="") as f:
        fila_restaurada = next(csv.DictReader(f))
    assert fila_restaurada["Estado"] == "APPROVED"
    assert fila_restaurada[archivo.COLUMNA_CAMBIO_ESTADO] > marca


def test_omitir_preserva_todas_las_filas_y_solo_cambia_la_marca_objetivo(tmp_path, monkeypatch):
    monkeypatch.setattr(archivo, "RUTA", str(tmp_path / "reportes" / "mercado_pago_sync.csv"))
    _write_csv(tmp_path / "reportes" / "mercado_pago_sync.csv", [
        _row("pago-1", "APPROVED", "2026-09-28 10:00:00"),
        _row("pago-2", "APPROVED", "2026-09-28 10:01:00"),
        _row("pago-3", "APPROVED", "2026-09-28 10:02:00"),
    ])

    assert archivo.omitir("pago-2")

    with open(archivo.RUTA, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = {row["ID de Pago"]: row for row in reader}
        assert reader.fieldnames == archivo.COLUMNAS
    assert set(rows) == {"pago-1", "pago-2", "pago-3"}
    assert rows["pago-1"]["Estado"] == "APPROVED"
    assert rows["pago-3"]["Estado"] == "APPROVED"
    assert rows["pago-1"][archivo.COLUMNA_CAMBIO_ESTADO] == "2026-09-28 10:00:00"
    assert rows["pago-3"][archivo.COLUMNA_CAMBIO_ESTADO] == "2026-09-28 10:02:00"
    assert rows["pago-2"]["Estado"] == "OMITIDO"
    assert rows["pago-2"][archivo.COLUMNA_CAMBIO_ESTADO] > "2026-09-28 10:02:00"


def test_restauracion_mas_reciente_gana_en_sincronizacion(tmp_path, monkeypatch):
    csv_local = tmp_path / "local" / "reportes" / "mercado_pago_sync.csv"
    root = tmp_path / "USB" / "CobroFacil_Nodo"
    csv_node = root / "reportes" / "mercado_pago_sync.csv"
    links_local = tmp_path / "local" / "reportes" / "mp_vinculos.json"
    monkeypatch.setattr(archivo, "RUTA", str(csv_local))
    monkeypatch.setattr(libro, "RUTA", str(links_local))

    _write_csv(csv_local, [_row("201", "APPROVED", "2026-09-29 09:30:00.000000")])
    _write_csv(csv_node, [_row("201", "OMITIDO", "2026-09-29 09:10:00.000000")])

    nodo.sincronizar_nodo(str(root))

    with csv_node.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        pago = next(reader)
        assert reader.fieldnames == archivo.COLUMNAS
    assert pago["Estado"] == "APPROVED"
    assert pago[archivo.COLUMNA_CAMBIO_ESTADO] == "2026-09-29 09:30:00.000000"


def test_nodo_configurado_ausente_no_se_crea(tmp_path, monkeypatch):
    from src.jefe.nodo_portable import motor_nodo

    root = tmp_path / "unidad_desconectada" / "CobroFacil_Nodo"
    monkeypatch.setattr(motor_nodo, "get_nodo_path", lambda: str(root))
    monkeypatch.setattr(motor_nodo, "estado_nodo", lambda path: "none")

    try:
        nodo.sincronizar_nodo_configurado()
    except FileNotFoundError as error:
        assert "unidad" in str(error)
    else:
        raise AssertionError("Debe informar que falta el nodo configurado")
    assert not root.exists()
