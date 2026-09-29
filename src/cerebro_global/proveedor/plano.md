# Plano — motor global de proveedores

## Función

`motor_proveedor.py`, clase `MotorProveedor`, sirve a la vista compartida `src/ui_global/proveedor/vista_proveedor.py` tanto desde admin como desde jefe.

## Flujo de datos

- `get_proveedores_unicos` y `load_proveedores`: jefe lee su base de Contabilidad; admin lee MariaDB conectada o, si no está disponible, una copia de solo lectura provista por `src/jefe/nodo_portable/espejo`.
- `save_proveedor`: requiere MariaDB disponible antes de crear filas en `romaneos`, `romaneo_items`, impactos de stock y el gasto o deuda según perfil.
- `pagar_proveedor`: requiere conexión con la tienda antes de modificar la deuda. El perfil jefe conserva su rutina `pay_debt` cuando la tienda está disponible.
- Sin red, admin no usa `punpro.db` como sustituto de la tienda. Si no existe copia del nodo, entrega historial vacío y la vista muestra que no hay copia disponible.

## Qué no cambiar

- No escribir compras ni pagos en la copia SQLite: es un espejo para consulta, no una cola de operaciones.
- No cambiar la selección de base de jefe, ni cruzar `general_debts` con `gastos`.
- No separar esta lógica por perfil: la misma vista global debe seguir siendo reutilizable.
