# Integración Contable con la TPV (Maestra)

Módulo encargado de automatizar la carga de datos en Contabilidad sacando la información directamente de la operación real de las cajas.
**Regla:** Contabilidad NO edita la base Maestra. Solo lee las ventas y los retiros, y los inserta en su propia SQLite como "Ingresos" y "Gastos".

## Función
`sincronizador.py`: Extractor diario que copia los ingresos (por medio de pago) y los costos de las mercaderías vendidas (Costo de Mercadería) leyendo `db_maestra` y guardándolos en `db_contabilidad`.

## Cómo funciona
1. El jefe o un temporizador activan la sincronización.
2. Se importan ambas conexiones a las bases de datos de forma aislada.
3. Se ejecutan consultas `SELECT` sobre el motor `db_maestra` (MariaDB/SQLite Tienda) para agrupar ventas.
4. Se procesan los resultados en memoria.
5. Se insertan usando llamadas aisladas o `conn.cursor().execute` nativo a través de `self.db_contabilidad.get_connection()`.

## Qué no cambiar
- **No mezclar las ejecuciones SQL de ambos motores.** `db_contabilidad` (del módulo Contabilidad) expone la conexión SQLite nativa, y NO tiene métodos como `.execute_query()` propios del motor de la tienda. El enrutamiento de consultas debe respetar el Aislamiento de Motores; lo de la maestra se consulta con `db_maestra.execute_query` y las escrituras locales se deben transaccionar explícitamente en `db_contabilidad` sin asumir que comparten métodos de abstracción.
