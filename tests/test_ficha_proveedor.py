"""El id de proveedor no entra en el producto ni en el nombre del romaneo."""

from src.motor_abastecimiento.enlace.puente_proveedor import resolver_proveedor
from src.proveedor_global.backend.ficha import codigo_visible, etiqueta, nombre_de_eleccion


def test_codigo_visible():
    assert codigo_visible(1) == "P00001"
    assert codigo_visible(12) == "P00012"


def test_el_romaneo_guarda_el_nombre():
    ficha = {"id": 12, "codigo": "P00012", "nombre": "La Serenísima", "telefono": ""}
    assert nombre_de_eleccion(etiqueta(ficha), ficha) == "La Serenísima"
    assert nombre_de_eleccion("Frigorífico", None) == "Frigorífico"


def test_el_producto_gana_al_departamento():
    mapas = [
        {
            "criterio_tipo": "departamento",
            "criterio_valor": "LACTEOS",
            "proveedor_nombre": "Del departamento",
            "proveedor_codigo": "P00001",
            "proveedor_id": 1,
        },
        {
            "criterio_tipo": "producto_id",
            "criterio_valor": "9",
            "proveedor_nombre": "Del producto",
            "proveedor_codigo": "P00002",
            "proveedor_id": 2,
        },
    ]
    assert resolver_proveedor(mapas, {"id": 9, "departamento": "Lacteos"})["nombre"] == "Del producto"
    assert resolver_proveedor(mapas, {"id": 4, "departamento": "Lacteos"})["codigo"] == "P00001"
    assert resolver_proveedor(mapas, {"id": 3, "departamento": "Pan"}) is None
