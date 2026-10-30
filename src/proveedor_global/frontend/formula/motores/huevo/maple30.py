"""Maple de 30 huevos. Un cajón son 12 de estas. No conoce a las otras."""

HUEVOS = 30
NOMBRE = "Maple 30 huevos"
CAJON = 360


def salen() -> int:
    if CAJON % HUEVOS != 0:
        raise ValueError("30 no cierra en 360")
    return CAJON // HUEVOS


def stock(cajones) -> float:
    from src.proveedor_global.frontend.formula.motores.carga import stock_de
    return stock_de(cajones, HUEVOS)


def cuadra() -> bool:
    return salen() * HUEVOS == CAJON
