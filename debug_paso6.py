import sys
import traceback
from PyQt6.QtWidgets import QApplication

try:
    app = QApplication(sys.argv)
    from src.cajero.paso6_cobro import Paso6Cobro
    w = Paso6Cobro(total=100.0, items_carrito=[])
    print("Paso6Cobro instanciado correctamente.")
except Exception as e:
    print("Error instanciando Paso 6:")
    traceback.print_exc()
