# Capa de compatibilidad: re-exporta desde la nueva ubicación en cerebro/
# Esto garantiza que cualquier import antiguo siga funcionando sin romper nada.
from src.motor_descuentos.cerebro.motor_ofertas import MotorOfertas
from src.motor_descuentos.cerebro.motor_combos import MotorCombos
from src.motor_descuentos.cerebro.motor_mayoreo import MotorMayoreo

__all__ = ["MotorOfertas", "MotorCombos", "MotorMayoreo"]
