# Planilla de reposición

Orquestador propio. El stock sube y baja sin saber que esta planilla existe. Pedidos la lee y no la escribe.

## Qué hace la carpeta
Después de cada venta o recepción, el stock ya quedó en `productos`. Este motor, en su hilo, mira ese stock contra el mínimo y el máximo y reescribe `planilla_reposicion`.

## Qué función, con el nombre real
* `MotorPlanilla.actualizar()`: pide la alarma a `productos_con_alarma_reposicion()`, calcula `cantidad_sugerida` y llama a `repo.reemplazar()`. Solo lo llama el hilo de esta carpeta.
* `MotorPlanilla.avisar()`: prende ese hilo si falta y pide un pase ya. No lee stock y no escribe la hoja. Lo usan el conteo de auditoría, el ingreso de recepción y el puente del piso, después de que su grabación ya salió bien.
* `MotorPlanilla.leer()`: lee solo `planilla_reposicion`.
* `MotorPlanilla.arrancar()`: prende `arrancar_hilo()`.
* `arrancar_hilo()` / `avisar_planilla()` / `_bucle()`: hilo demonio. Limpia el aviso, actualiza, y espera 15 segundos o hasta el próximo `avisar()`.
* `repo.reemplazar()`: escribe primero `planilla_reposicion_borrador` con un solo `execute_many`, y otro para la tabla viva. Recién cuando ese borrador está completo pisa `planilla_reposicion`. Si la lectura del stock falló, `actualizar()` no llama a `reemplazar()` y la hoja anterior queda. `producto_id` es el id del producto. No entra `formula:Pollo`: esa fila se descarta. `asegurar()` corre una vez por proceso y deja la columna en texto por si el id es un código de barras.
* La cantidad: techo menos stock si hay techo por encima del piso. Piso menos stock si no hay techo. Cero si no hay piso ni techo (`motivo` = `sin_piso`).

## Cómo funciona, en el orden en que corre
1. La pantalla de proveedores llama a `arrancar()`. El cajero no lo llama.
2. El hilo lee el stock que la venta ya guardó. No entra en la venta.
3. Reescribe la planilla con los que están en cero o bajo el piso, y la cantidad hasta el techo.
4. Si alguien cargó stock en auditoría o en recepción, o guardó piso y techo, llama a `avisar()`. El hilo corta la espera y vuelve a leer. Si ese aviso falla, el stock ya guardado sigue igual y el próximo pase de 15 segundos lo ve.
5. `preguntar_alarma()` de abastecimiento llama a `leer()`. Si esta planilla falla, pedidos sigue vacío.

## Qué devuelve cuando falla
`actualizar()` devuelve `0`. `leer()` devuelve `[]`. El hilo sigue al próximo pase. La venta no se entera.

## Qué no debe cambiar una mejora futura
* Esta hoja pide stock y copia stock. No corre la fórmula.
* No llamar a `avisar()` ni a `actualizar()` desde `descontar_stock` ni desde el cajero.
* No escribir `productos` desde acá.
* Pedidos no llama a `actualizar()` ni a `avisar()`. Solo lee.
* Auditoría, recepción y piso no llaman a `actualizar()`. Solo avisan.
