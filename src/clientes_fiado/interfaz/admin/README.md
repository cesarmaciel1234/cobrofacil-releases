# Admin

No hay ventana acá. `src/admin/clientes` pinta la lista, el alta, la ficha, el límite, el abono y el historial.

Esas acciones llaman `cerebro`: `buscar`, `alta_regular`, `actualizar_existente`, `actualizar_ficha`, `fijar_limite`, `abonar`, `movimientos` y `ultimo_cargo`.

El recálculo de compras fiadas sigue leyendo su consulta en `dialogo_recalculo_fiado.py`. No guarda la deuda.
