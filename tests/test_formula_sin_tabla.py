def test_si_falta_la_orden_pregunta_una_sola_vez():
    from src.proveedor_global.frontend.formula.motores import orden, pregunta

    pregunta._AUSENTES.clear()

    class Base:
        def __init__(self):
            self.n = 0
            self.last_error = ""

        def execute_query(self, *_args, **_kwargs):
            self.n += 1
            self.last_error = "(1146, \"Table 'punpro_db.formula_orden' doesn't exist\")"
            return []

    base = Base()
    assert orden.traer(base, "Pollo")["cortes"] == []
    primera = base.n
    assert orden.traer(base, "Cerdo")["cortes"] == []
    assert base.n == primera
    orden.tabla_presente()
    orden.traer(base, "Pollo")
    assert base.n == primera + 1
    pregunta._AUSENTES.clear()
