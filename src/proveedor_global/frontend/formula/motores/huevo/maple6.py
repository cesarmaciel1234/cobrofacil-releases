"""De 6 huevos. Un cajón son 60. No conoce a las otras."""

HUEVOS = 6
NOMBRE = "Maple 6 huevos"
CAJON = 360


def salen() -> int:
    if CAJON % HUEVOS != 0:
        raise ValueError("6 no cierra en 360")
    return CAJON // HUEVOS


def stock(cajones) -> float:
    from src.proveedor_global.frontend.formula.motores.carga import stock_de
    return stock_de(cajones, HUEVOS)


def cuadra() -> bool:
    return salen() * HUEVOS == CAJON
