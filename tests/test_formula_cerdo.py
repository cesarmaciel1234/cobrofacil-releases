"""La receta de cerdo no se guarda si el corte o el bulto no cierran."""

from src.jefe.promedios.receta import revisar
from src.proveedor_global.frontend.formula.motores.orden import _interpretar


def _fila(nombre, kilos, codigo=""):
    fila = [nombre, kilos] + [""] * 11
    fila.append(codigo)
    return fila


def test_sin_kilos_no_guarda():
    filas = [_fila("Pechito", "10"), _fila("Paleta", "")]
    assert revisar(filas, "100") == "Paleta no tiene kilos."


def test_bulto_de_cien_acepta_pesos_distintos():
    filas = [
        _fila("Pechito", "10"),
        _fila("Bondiola", "5"),
        _fila("Matambre", "3"),
        _fila("Carré", "8"),
        _fila("carnaza", "12"),
    ]
    assert revisar(filas, "100") == ""


def test_cortes_que_pasan_el_bulto_no_guardan():
    assert "suman" in revisar([_fila("Pechito", "80"), _fila("Paleta", "30")], "100")


def test_corte_repetido_no_guarda():
    assert revisar([_fila("Bondiola", "5"), _fila("bondiola", "4")], "100") == "bondiola está repetido."


def test_sin_bulto_no_guarda():
    assert "bulto" in revisar([_fila("Pechito", "10")], "").lower()


def test_la_orden_conserva_el_bulto_y_el_codigo():
    datos = _interpretar({
        "cortes": [["Paleta", 6, "741"]],
        "merma": 94,
        "costo_kg": 1200,
        "kilos_bulto": 100,
    })
    assert datos["kilos_bulto"] == 100
    assert datos["cortes"] == [("Paleta", 6.0)]
    assert datos["codigos"]["PALETA"] == "741"
