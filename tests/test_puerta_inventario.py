class _Rota:
    def execute_query(self, *a, **k):
        raise RuntimeError("base caída")

    def execute_non_query(self, *a, **k):
        raise RuntimeError("base caída")

    def get_connection(self):
        raise RuntimeError("base caída")


def test_si_la_base_cae_la_puerta_no_rompe_al_modulo():
    from src.motor_inventario.puerta import borrar, catalogo, fijar, por_id, precios, sumar

    rota = _Rota()
    assert por_id(1, rota) is None
    assert catalogo(rota) == []
    assert precios([1], rota) == {}
    assert fijar(rota, "1", 4) is False
    assert sumar(rota, "1", 2) is False
    assert borrar("") is False
