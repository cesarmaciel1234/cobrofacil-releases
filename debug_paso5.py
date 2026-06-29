import sys
import traceback
from PyQt6.QtWidgets import QApplication

try:
    app = QApplication(sys.argv)
    from src.cajero.paso5cobranza import CentroCobranzasPanel
    w = CentroCobranzasPanel()
    print("CentroCobranzasPanel instanciado correctamente.")
except Exception as e:
    print("Error instanciando Paso 5:")
    traceback.print_exc()
