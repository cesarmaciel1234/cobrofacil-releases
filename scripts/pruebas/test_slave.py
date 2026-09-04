import os
import sys

from src.central_red_global.motor_red import MotorRed
from src.base_de_datos.database import db_manager

def test():
    print("Testing connection to 192.168.0.5 as ESCLAVA...")
    motor = MotorRed()
    
    # Intenta convertir en esclava apuntando a 192.168.0.5
    ok, msg = motor.convertir_en_esclava("192.168.0.5")
    
    print(f"Result: {ok}")
    print(f"Message: {msg}")
    
    print("\nDetalles del estado de red actual:")
    print(motor.obtener_estado_red())

if __name__ == "__main__":
    test()
