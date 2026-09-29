# Plano — proveedor global

## Frente

`vista_proveedor.py`, clase `VistaProveedor`, es la pantalla compartida de compras/romaneos. La abre el admin desde `src/admin/proveedores` y el jefe dentro de Contabilidad → Proveedores.

Presenta el formulario para capturar un romaneo, su total, el selector de condición de pago y el historial. Sin conexión con la tienda, el formulario de escritura queda deshabilitado; el historial disponible se consulta en modo lectura.

## Fondo

La vista delega consultas y operaciones a `src/cerebro_global/proveedor/motor_proveedor.py`.

- Admin conectado: lee y escribe en MariaDB mediante `db_manager`.
- Admin sin red: lee desde `espejo.fuente()` cuando existe una copia interna o del nodo. La copia del negocio incluye `gastos`, `romaneos` y `romaneo_items`.
- Jefe: consulta sus deudas a proveedores desde el `db_jefe` de Contabilidad, que conserva su archivo portable. La consulta no cambia de base al compartir la pantalla.
- Sin conexión autoritativa: compras y pagos quedan bloqueados. No se escribe en `punpro.db` ni se intenta sincronizar una compra sin su romaneo, deuda e impacto de stock.

## Qué no cambiar

- No reemplazar el widget compartido por pantallas duplicadas para admin y jefe.
- No presentar el historial local `punpro.db` como si fuera el nodo o la tienda.
- No habilitar una compra offline parcial: el romaneo, su detalle, el registro de gasto/deuda y el desposte deben quedar coherentes.
