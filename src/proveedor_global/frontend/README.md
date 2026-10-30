# Frontend - Vista Proveedor, Recepción y Abastecimiento

Esta subcarpeta contiene la capa de presentación de la gestión de proveedores y abastecimiento.

## Qué hace la carpeta
Provee el ingreso `VistaProveedor`. Al abrirlo hay seis tarjetas. Cada proceso vive en su carpeta: `pedido/`, `carga/`, `fichas/`, `pago/`, `historial/` y `formula/`.

## Qué función, con el nombre real
* `VistaProveedor._ir(codigo)`: abre una tarjeta. `hub` son las seis. `carga` abre escáner y peso. `formula` abre las categorías y después la lista que compone cada una.
* `VistaProveedor._volver()`: desde un subproceso vuelve a su proceso; desde un proceso, a las seis tarjetas; desde ahí, al dashboard.
* `pedido/panel.py`: `PanelPedidosAutomaticos` y `DialogoAltaProveedor`.
* `carga/recepcion.py`: `PanelRecepcionRapida`. La carga por peso sigue armada en `VistaProveedor`.
* `fichas/panel.py`: `DialogoProveedoresActivos` (con `embebido=True` dentro de la tarjeta) y el historial. «Cargar proveedor» está en esa tarjeta. El nombre abre `DialogoHistorialProveedor`. «Productos asociados» busca por nombre o código, elige uno o varios y «Desenlazar» los saca del proveedor. La pistola, con un solo resultado y Enter, abre esa confirmación. «Editar datos» cambia nombre y teléfono.
* `VistaProveedor._pago_centralizado(en_pagina=True)`: la tarjeta de pago, no un cuadro suelto.
* `VistaProveedor.cargar_datos()`: Consulta a `MotorProveedor.load_proveedores` y puebla la tabla histórica con formato de moneda, estado de deuda y botón `👁️ Ver Remito` / `💳 Pagar Deuda`.
* `PanelPedidosAutomaticos.refrescar_datos()`: arranca `HiloReposicion`. No llama al inventario en el hilo de la ventana.
* `PanelPedidosAutomaticos._pintar_resumen()`: pinta el resumen que el hilo ya trajo. Si vino vacío, la pantalla queda en cero.
* `PanelPedidosAutomaticos._al_editar_celda()`: al cambiar «A Pedir», o el mínimo y el máximo, rearma el WhatsApp en el momento. No escribe `productos`.
* `PanelPedidosAutomaticos._guardar_piso()`: arranca `HiloGuardarPiso`. Ese hilo llama a `guardar_piso_techo`, que graba solo `stock_minimo` y `stock_maximo` y después avisa a la planilla.
* `PanelRecepcionRapida._build_ui()`: Construye la estructura en espejo de dos columnas: izquierda con datos de remito + escáner + tabla en vivo, derecha con card oscura de totales y confirmación de stock.
* `PanelRecepcionRapida._init_buscador_asistido()`: Prepara la lista clara de coincidencias. Flota sobre la ventana, debajo de la barra verde, para que la tabla de artículos no la tape.
* `plata()`: llama a `texto()` de `backend/moneda.py`. El símbolo es el de la tienda, no un peso fijo.
* `_dia()`: la columna Fecha del histórico muestra día/mes/año. El combo de proveedor arranca en `Sin Proveedor (Proveedor General)`.
* `PanelRecepcionRapida._ejecutar_busqueda_en_vivo()`: Consulta a `RecepcionService.buscar_productos_coincidentes` y despliega la lista con Producto, Costo y Stock.
* `PanelRecepcionRapida._seleccionar_item_busqueda()`: Toma el producto elegido (por Enter o clic), le aplica el multiplicador (`7*`) y lo añade a la planilla.
* `DialogoVincularProveedor`: el departamento lo pide un hilo a `MotorDepartamentos`. El producto busca por el nombre, por una palabra siguiente y por código de barras; la pistola confirma con Enter. Solo dentro del departamento elegido. Si no hay, lo dice y no trae otro sector. Al elegir una fila libre la lista se cierra. Si ya tiene proveedor, la fila queda en ámbar y no se enlaza a otro. Enter en el proveedor o en el teléfono guarda el vínculo. El nombre del proveedor arranca vacío. `PanelPedidosAutomaticos._pintar_resumen` deja «Todos» primero para que asignar un proveedor no oculte el resto de los faltantes.
* `PanelRecepcionRapida.recargar_proveedores()`: lista las fichas ya cargadas. Acá no se crea proveedor.
* `PanelRecepcionRapida._eliminar_item(idx)`: Quita un producto escaneado puntualmente con el botón `❌`.
* `PanelRecepcionRapida._confirmar_ingreso()`: Ejecuta en un solo tiro el ingreso de stock, actualización de costo y guardado de compra, emitiendo `compra_guardada` para actualizar el historial inferior.

## Cómo funciona, en el orden en que corre
1. Al entrar a la Pestaña 2 (Recepción Rápida), el operador ve la barra de escaneo lista y abajo el histórico de compras previas.
2. Escanea productos con la pistola o tipea multiplicadores (ej: `12*77900401` + Enter).
3. Si el costo unitario subió respecto al anterior, edita el importe en la tabla.
4. Elige si es "A Pagar (Deuda en Cta. Cte.)" o "Contado".
5. Hace clic en "CONFIRMAR INGRESO A STOCK":
   - El stock y el costo se actualizan en `productos`.
   - La tabla de escaneo se vacía para el próximo remito.
   - La tabla inferior se refresca inmediatamente mostrando el nuevo remito con su estado y saldo restante.

## Qué devuelve cuando falla
* Atrapa excepciones y muestra cuadros de diálogo amigables (`QMessageBox.warning` o `critical`) sin clavar la pantalla.

## Qué no debe cambiar una mejora futura
* No incluir sentencias SQL directas en el frontend. Toda operación sobre datos viaja por `recepcion_service.py`, `motor_proveedor.py` o `motor_abastecimiento`.
