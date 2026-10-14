# Lógica F3

- `historial_controller.py` — clase `HistorialController`. `get_ventas` filtra fecha, hora, medio, texto. `get_detalle_venta`. `cancelar_venta` → `db_manager.cancelar_venta_transaccional`. `plan_devolucion` / `texto_devolucion` arman el aviso de efectivo o de anular deuda. `reimprimir_ticket` llama la impresora. Si cancelar falla, el diálogo muestra error y el ticket sigue COMPLETADA.
- `formato.py` — `fmt_moneda`, `fecha_a_texto`.
- `teclas.py` — `aplicar_tecla`: Esc cierra.

Qué no cambiar: no insertar RETIRO de caja acá; lo hace la transacción de ventas.
