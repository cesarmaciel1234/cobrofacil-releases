import sys
import datetime
from PyQt6.QtWidgets import QApplication
from src.contabilidad.jefe_contabilidad import JefeContabilidad
from src.contabilidad.database import Database

app = QApplication(sys.argv)
try:
    print('Iniciando Database...')
    db = Database()

    print('Instanciando JefeContabilidad...')
    jefe = JefeContabilidad()

    print('Probando cargar_datos_periodo(\'Hoy\')...')
    jefe.cargar_datos_periodo('Hoy')
    print('  -> desde:', jefe._desde)
    print('  -> hasta:', jefe._hasta)

    print('Probando vista_resumen (get_stats)...')
    res = jefe._db.get_stats(jefe._desde, jefe._hasta)
    print('  -> stats ok')

    print('Probando vista_gastos (get_expenses)...')
    gastos = jefe._db.get_expenses()
    print('  -> cant gastos local:', len(gastos) if gastos else 0)

    print('Probando vista_ingresos (get_income)...')
    ing = jefe._db.get_income(jefe._desde, jefe._hasta)
    print('  -> cant ingresos filtrados:', len(ing) if ing else 0)

    print('\nTodo se ejecutó SIN ERRORES!')
    sys.exit(0)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
