
import sys
from PyQt6.QtWidgets import QApplication
import traceback

try:
    from src.contabilidad.jefe_contabilidad import JefeContabilidad
    app = QApplication(sys.argv)
    j = JefeContabilidad()
    j._load_db_and_build()
    j._load_resumen()
    print('SUCCESS')
except Exception as e:
    traceback.print_exc()

