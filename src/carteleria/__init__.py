"""Módulo de cartelería digital (monitor secundario)."""


def __getattr__(name):
    if name == "CarteleriaMain":
        from src.carteleria.el_cuello import CarteleriaMain
        return CarteleriaMain
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["CarteleriaMain"]
