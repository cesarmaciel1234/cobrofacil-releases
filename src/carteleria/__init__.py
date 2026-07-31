"""Módulo de cartelería digital (monitor secundario)."""

# Import lazy — no cargar CarteleriaMain al importar el paquete.
# Esto evita que un error de sintaxis en un sub-módulo crashee toda la app.
def _get_main():
    from src.carteleria.motor_carteleria.main_board import CarteleriaMain
    return CarteleriaMain

__all__ = ["CarteleriaMain"]
