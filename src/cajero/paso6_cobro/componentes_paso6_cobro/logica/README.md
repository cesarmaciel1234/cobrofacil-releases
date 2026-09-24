# Lógica del cobro

Valida el monto. Efectivo es el único que pide vuelto. No pinta las tarjetas.

`CobroController.validar_monto_suficiente` es estático. Recibe método, total y montos. No usa `db_manager`. Un `ValueError` devuelve `(None, None)`.

`CobroController.calcular_vuelto_y_totales` hace `max(0, total - descuento + recargo)`.

`CobroController.procesar_y_guardar_venta` arma el diccionario y llama `persistir_cobro`. La escritura no está en este archivo.

No convertir `validar_monto_suficiente` en método de instancia para inyectar la base.
