# Reporte Financiero

Submódulo de Reportes que genera las estadísticas y KPIs de ventas (resumen por día, mes, medios de pago, ganancias, etc.).

## Función
`consulta.py`: Expone las funciones de recolección de datos (como `kpis_rango` y `payload_reporte_global`) usando los filtros de periodo.

## Cómo funciona
1. La vista (`vista_financiero.py`) llama a `cargar_datos(periodo)`.
2. Las consultas a la base de datos se hacen a través de la función `_db()`, que garantiza el **aislamiento de motores**.
3. Si la red está activa, `_db()` devuelve una conexión a MariaDB (`db_manager`).
4. Si la red está caída (microcorte) y el panel detecta que está offline, `_db()` devuelve `espejo.fuente()` (el Lector del archivo SQLite de solo lectura `espejo_tienda.db`).
5. Se renderizan las gráficas sin interrumpirse, usando siempre los datos reales de la tienda (online o en copia espejo), nunca de la base de cobro offline.

## Qué no cambiar
- **No reemplazar `_db().execute_...` por llamadas directas a `db_manager.execute_...` en la vista financiera.** Llamar a `db_manager` directamente en la vista provoca que, ante una falla de red, el reporte consulte `punpro.db` (la base de caja offline), arrojando gráficos en **$0.00**. La lectura debe pasar siempre por el enrutador `_db()` para mantener separado el motor de la tienda del motor de cobro local.
