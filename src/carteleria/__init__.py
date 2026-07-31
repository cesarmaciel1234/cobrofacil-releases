"""Módulo de cartelería digital (monitor secundario)."""

# Import lazy — no cargar CarteleriaMain al importar el paquete.
def _get_main():
    from src.carteleria.motor_carteleria.main_board import CarteleriaMain
    return CarteleriaMain

__all__ = ["CarteleriaMain"]
