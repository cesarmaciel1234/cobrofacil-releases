from src.motor_inventario.planilla import repo


def test_la_planilla_no_guarda_formula_pollo():
    filas = repo._filas_producto([
        {"id": "formula:Pollo", "nombre": "Caja de pollo"},
        {"id": 44, "nombre": "Yerba", "cantidad_sugerida": 2},
    ])
    assert [f["id"] for f in filas] == ["44"]
    params = repo._params(filas, "2026-10-30 18:49:14")
    assert params[0][0] == "44"
    assert params[0][2] == "Yerba"


def test_replica_offline_usa_id_venta():
    from pathlib import Path

    texto = Path(__file__).resolve().parents[1].joinpath(
        "src/base_de_datos/offline_sync.py"
    ).read_text(encoding="utf-8")
    assert "WHERE id_venta >=" in texto
    assert "SELECT id, id_venta, id_producto" in texto
    assert "WHERE venta_id >=" not in texto
