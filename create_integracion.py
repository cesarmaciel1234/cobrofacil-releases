import os

base_dir = 'src/contabilidad/integracion_maestra'
os.makedirs(base_dir, exist_ok=True)

with open(os.path.join(base_dir, '__init__.py'), 'w', encoding='utf-8') as f:
    f.write('')

plano_content = """# Integración con la Base Maestra

**Objetivo:** Este módulo es un puente unidireccional. Extrae datos de la operación real de la tienda (Ventas, Turnos, Movimientos de Caja) almacenados en MariaDB (base Maestra), y los traduce a formatos contables (Ingresos, Gastos) para inyectarlos en la base de datos aislada de Contabilidad (SQLite).

## Flujo de Datos

1. **Origen:** `src.base_de_datos.core.connection.db_connection` (MariaDB u offline SQLite).
2. **Transformación:** Las consultas agrupan totales diarios por método de pago, retiros y sobrantes/faltantes.
3. **Destino:** `src.contabilidad.database.Database` (SQLite local de contabilidad).

## Módulos

- `sincronizador.py`: Contiene la clase `SincronizadorMaestra` con los métodos preparados para hacer el `fetch` de MariaDB y pasarlo al DB de contabilidad.

## Uso futuro
En el `jefe_contabilidad.py` se pondrá un botón "Sincronizar Ventas de Hoy" o se ejecutará al iniciar el panel.
"""

with open(os.path.join(base_dir, 'plano.md'), 'w', encoding='utf-8') as f:
    f.write(plano_content)

readme_content = """# Integración Contable con la TPV (Maestra)

Módulo encargado de automatizar la carga de datos en Contabilidad sacando la información directamente de la operación real de las cajas.
**Regla:** Contabilidad NO edita la base Maestra. Solo lee las ventas y los retiros, y los inserta en su propia SQLite como "Ingresos" y "Gastos".
"""

with open(os.path.join(base_dir, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme_content)

sync_content = """import logging
from datetime import date
from src.base_de_datos.core.connection import db_connection
from src.contabilidad.database import Database

logger = logging.getLogger(__name__)

class SincronizadorMaestra:
    \"\"\"
    Se encarga de leer de MariaDB (la TPV) e insertar en la base de Contabilidad.
    \"\"\"
    def __init__(self, db_contabilidad: Database):
        self.db_contabilidad = db_contabilidad

    def traer_ventas_del_dia(self, fecha: date = None):
        \"\"\"
        Agrupa las ventas de la TPV de una fecha (o de hoy) por medio de pago, 
        y las inyecta como Ingresos en Contabilidad.
        \"\"\"
        if not fecha:
            fecha = date.today()
        
        fecha_str = fecha.strftime(\"%Y-%m-%d\")
        
        conn_maestra = db_connection.get_connection()
        if not conn_maestra:
            logger.error(\"No hay conexión a la base maestra para sincronizar ventas.\")
            return False

        try:
            cursor = conn_maestra.cursor()
            # Esta consulta se ajustará a la estructura real de ventas de la TPV
            # Por ejemplo:
            # cursor.execute(\"\"\"
            #     SELECT forma_pago, SUM(total) as total
            #     FROM ventas 
            #     WHERE DATE(fecha) = ?
            #     GROUP BY forma_pago
            # \"\"\", (fecha_str,))
            # resultados = cursor.fetchall()
            
            # TODO: Cuando se active, iterar los resultados y usar self.db_contabilidad.add_income(...)
            
            logger.info(f\"Ventas del {fecha_str} preparadas para sincronizar.\")
            return True
        except Exception as e:
            logger.error(f\"Error al sincronizar ventas: {e}\")
            return False
        finally:
            if hasattr(conn_maestra, 'close') and type(conn_maestra).__name__ == 'Connection':
                pass # Si es sqlite se puede cerrar, si es mariadb pool no se cierra directo. En TP PRO se maneja solo.

    def traer_retiros_y_cierres(self, fecha: date = None):
        \"\"\"
        Lee los movimientos de caja (retiros, faltantes) de MariaDB
        y los inyecta como Gastos o Ingresos Extra en Contabilidad.
        \"\"\"
        pass
"""

with open(os.path.join(base_dir, 'sincronizador.py'), 'w', encoding='utf-8') as f:
    f.write(sync_content)

print('Estructura piramidal y documentacion creada con exito.')
