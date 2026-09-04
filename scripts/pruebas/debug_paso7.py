import sys
import traceback
from PyQt6.QtWidgets import QApplication

try:
    app = QApplication(sys.argv)
    from src.cajero.paso7_cierre import Paso7CierreCaja
    
    # We won't call .show() to avoid MariaDB blocking if it tries to do heavy queries 
    # but we will instantiate it. Wait, setup_ui executes on __init__, so queries in _get_data will run.
    w = Paso7CierreCaja()
    print("Paso7CierreCaja instanciado correctamente.")
except Exception as e:
    print("Error instanciando Paso 7:")
    traceback.print_exc()
