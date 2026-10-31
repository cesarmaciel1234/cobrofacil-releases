# Plano — auditoría de inventario

Esta carpeta es donde arranca la rama. El frente está acá. El fondo está en `src/cerebro_global/auditoria/`.

## Frente

Pantalla: `auditoria_main.py`, clase `AuditoriaMain`. La abre el admin en `Screen.AUDITORIA` (25) de `src/main_window.py`.

Ecosistema: pide el listado al conector, envía el conteo como SET de stock de un producto real. No importa el motor de ofertas ni la fórmula. No inserta ids sintéticos.

Al mostrarse, `showEvent` aplica el perfil, el tema claro u oscuro y a los 80 ms pone el foco en el buscador.

`_es_lectura` es verdadero solo si el rol es `cajero`. Ese perfil ve la lista y no puede sumar conteos ni aplicar stock. Admin y jefe sí.

`cargar_datos` pide el inventario al conector y arma la tabla. Columnas: id, código, nombre, departamento, stock del sistema, conteo real, diferencia. Letras de góndola (`src/utils/letra.py`): id/código Consolas Bold, nombre y stock Segoe UI Bold. El stock del sistema no se edita. El conteo real, en admin, nace vacío y en ámbar. En el id de la fila se guardan `es_pesable` y `unidad`.

`_info_unidad` elige la unidad:

- metros si la unidad es MT, M, METRO o METROS, o el departamento dice textil o tela
- kilos si es pesable o la unidad es KG, KILO o KILOS
- litros si es LT, L, LITRO o LITROS
- cajas si es CJ, CAJA o CAJAS
- si no, unidades

Escanear (`_on_codigo_escaneado`) soporta multiplicador (`10*779001` o `5*Alitas` vía `BarcodeParser`) y busca la fila por id, código exacto o parte del código. Un código de barras de 8 dígitos o más abre el diálogo a los 180 ms sin necesidad de Enter. Abre `DialogoConteo` precargando la cantidad escaneada. El cajero no entra.

Doble clic o Enter sobre una fila también abre `DialogoConteo`. El teclado escribe el número con coma. `valor()` lo pasa a float. Guardar con Enter (teclado físico o numpad) llama `_aplicar_conteo_fila`: SET de stock en la BD de forma inmediata, pinta la fila en verde, recalcula diferencias y KPIs en vivo, y devuelve el foco instantáneamente al buscador para disparo continuo con pistola láser.

Al cambiar el conteo, `_on_item_changed` calcula diferencia = conteo − stock del sistema. Azul si sobra, rojo si falta. `_actualizar_kpis` cuenta SKU, contados, faltante y sobrante con tipografía de góndola peso 900.

El filtro de texto busca en id, código, nombre y departamento. La vista puede ser todos, solo contados o solo con diferencia.

Barra inferior empresarial limpia y automática:
- Se eliminaron los botones redundantes `EDITAR CONTEO` y `CONFIRMAR Y APLICAR AJUSTES` (cada conteo es 100% automático y en vivo al dar Enter).
- `📋 HISTORIAL DE AJUSTES`: abre el diálogo avanzado `DialogoHistorialAuditoria` (`dialogo_historial.py`). Cuenta con:
  - Botón nativo de maximizar `[🗖]` al lado de la `[X]` en la barra de título de Windows y botón manual `🗖 PANTALLA COMPLETA` / `🗗 RESTAURAR`.
  - Filtro por Producto (selector desplegable con conteo de movimientos por artículo).
  - Buscador en tiempo real por texto libre (producto, PLU/ID, código de barras, usuario o motivo).
  - Filtro por Responsable / Usuario y por sentido de diferencia (Faltantes, Sobrantes, Exactos).
  - 4 tarjetas KPI en vivo (Registros, Productos, Faltante acumulado y Sobrante acumulado).
  - Exportación directa del historial filtrado a CSV (`UTF-8-SIG`).
- `📊 EXPORTAR AUDITORÍA (CSV / Excel)`: descarga el reporte completo en formato CSV UTF-8-SIG compatible con Excel con estado de cada ítem (Exacto, Faltante, Sobrante, Pendiente).
- Badge de estado: `⚡ Auditoría Automática en Vivo · Cada conteo se guarda e impacta el stock al instante`.

## Fondo

El conector es `obtener_conector_auditoria()` en `motor_conector_auditoria.py`. Hay una sola instancia.

`obtener_inventario_para_auditoria` usa una caché de 15 segundos. Si se fuerza o venció, `_actualizar_cache` lee `MotorAuditoria.obtener_inventario`: `SELECT` de `productos` ordenado por departamento y nombre. Si eso falla, cae a `MotorCatalogo.obtener_productos`.

`solicitar_ajuste_stock` lee el producto vivo con `MotorAuditoria.leer_producto` (SELECT en la misma base del UPDATE). No depende del catálogo para aplicar. Rechaza stock negativo. Si la diferencia es cero, no escribe. Si hay diferencia:

1. `MotorAuditoria.aplicar_ajuste_stock` hace un solo `UPDATE productos SET stock = ? WHERE id = ?`. Es un SET al conteo, no una resta de venta.
2. Después `registrar_ajuste` hace un INSERT en `auditorias_inventario`. Ese insert no vuelve a tocar `productos.stock`.
3. Se invalida la caché del conector y la del catálogo global.
4. `MotorPlanilla.avisar()` despierta el hilo de la planilla. Este conector no llama a `actualizar()` y no escribe `planilla_reposicion`. Si la planilla no contesta, el stock contado queda.
5. La consola del servidor lee `auditorias_inventario` en `punpro.db` y en la réplica. No escribe un archivo aparte y no mete el conteo en la cola de cambios.

`aplicar_lote_ajustes` repite el `SET` producto por producto y avisa una sola vez al final. No llama `procesar_auditoria` después del UPDATE: eso volvería a hacer el SET y podría pisar una venta del medio.

`procesar_auditoria` existe en el motor y también hace SET más log. No usarlo encima de `solicitar_ajuste_stock`.

No usar `guardar_producto` para este ajuste: ese update puede pisar departamento u otros campos.

La venta no pasa por acá. El descuento de una venta está en `descontar_stock`. Si `opt_stock_negativo` está apagado, el update exige `stock >= cantidad`. Si otra caja se llevó el resto, la venta se deshace con `SinStock`.

## Qué no cambiar

- El log no escribe `productos.stock`.
- Cancelar una venta restaura stock solo con `WHERE id = ?`. No sumar `OR codigo = ?`.
- El cajero en esta pantalla es solo lectura.
