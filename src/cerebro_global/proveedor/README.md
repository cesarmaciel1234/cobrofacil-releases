# Motor global de proveedores

`motor_proveedor.py` contiene `MotorProveedor`, la lógica compartida de consulta y registro usada por la vista de proveedores.

- Admin consulta MariaDB cuando está disponible y, sin conexión, usa únicamente el espejo de solo lectura del nodo.
- Jefe sigue consultando las deudas de su base portátil de Contabilidad.
- Las escrituras en la tienda usan una conexión MariaDB fija con fallback a SQLite desactivado. Para Admin, romaneo, detalle, impacto de stock y gasto/deuda se guardan en una transacción de MariaDB. Jefe conserva su registro contable en `db_jefe`.
- Las escrituras offline no se guardan como operaciones pendientes: la vista indica que se requiere conexión.

No usar `punpro.db` como sustituto del espejo para mostrar datos de la tienda ni escribir operaciones de compra en el espejo.
