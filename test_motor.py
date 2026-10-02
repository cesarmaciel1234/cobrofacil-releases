import sys
import datetime
from PyQt6.QtWidgets import QApplication
from src.contabilidad.jefe_contabilidad import JefeContabilidad

app = QApplication(sys.argv)
jefe = JefeContabilidad()

# Force load
jefe._load_db_and_build()

print("Motor status:", hasattr(jefe, 'motor_sync'))

print('\nEjecutado!')
sys.exit(0)
