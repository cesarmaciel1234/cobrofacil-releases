# Vista global de proveedores

`vista_proveedor.py` contiene `VistaProveedor`, la pantalla compartida de Admin y Jefe para consultar proveedores, registrar romaneos y revisar gastos/deudas.

- La vista carga datos y registra operaciones mediante `src/cerebro_global/proveedor/motor_proveedor.py`.
- Sin conexión con MariaDB, presenta la copia del nodo en modo solo lectura y deshabilita el formulario y los pagos.
- Jefe conserva su base portátil contable; compartir la vista no cambia su origen de datos.

No agregar escrituras offline en esta vista ni tratar la copia del nodo como una cola de operaciones.
