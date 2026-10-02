# Integración Contable con la TPV (Maestra)

Módulo encargado de automatizar la carga de datos en Contabilidad sacando la información directamente de la operación real de las cajas.
**Regla:** Contabilidad NO edita la base Maestra. Solo lee las ventas y los retiros, y los inserta en su propia SQLite como "Ingresos" y "Gastos".
