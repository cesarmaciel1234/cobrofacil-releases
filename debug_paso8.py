import sys
import traceback
from PyQt6.QtWidgets import QApplication

try:
    app = QApplication(sys.argv)
    from src.cajero.paso8_historial import DialogoHistorialDia
    w = DialogoHistorialDia()
    print("DialogoHistorialDia instanciado correctamente.")
except Exception as e:
    print("Error instanciando Paso 8:")
    traceback.print_exc()
