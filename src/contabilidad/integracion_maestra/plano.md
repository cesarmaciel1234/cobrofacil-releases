# Integración con la Base Maestra

**Objetivo:** Este módulo es un puente unidireccional. Extrae datos de la operación real de la tienda (Ventas, Turnos, Movimientos de Caja) almacenados en MariaDB (base Maestra), y los traduce a formatos contables (Ingresos, Gastos) para inyectarlos en la base de datos aislada de Contabilidad (SQLite).

## Flujo de Datos

1. **Origen:** `src.base_de_datos.core.connection.db_connection` (MariaDB u offline SQLite).
2. **Transformación:** Las consultas agrupan totales diarios por método de pago, retiros y sobrantes/faltantes.
3. **Destino:** `src.contabilidad.database.Database` (SQLite local de contabilidad).

## Módulos

- `sincronizador.py`: Contiene la clase `SincronizadorMaestra` con los métodos preparados para hacer el `fetch` de MariaDB y pasarlo al DB de contabilidad.

## Uso futuro
En el `jefe_contabilidad.py` se pondrá un botón "Sincronizar Ventas de Hoy" o se ejecutará al iniciar el panel.
