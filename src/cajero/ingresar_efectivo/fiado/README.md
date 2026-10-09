# Fiado

Cobra deudas. La consulta está en `consulta.py` y solo devuelve clientes con saldo mayor a un centavo. El DNI lo normaliza `cerebro`. La lista muestra nombre y DNI; oculta importes hasta seleccionar al cliente (seguridad para pantallas expuestas al público). La ficha seleccionada deja visibles nombre, DNI, contacto y deuda, y enfoca el monto a abonar. Al elegir desde la lista, el foco va al monto y selecciona su contenido para reemplazarlo directamente. Si hay varios resultados, Enter lleva a la lista; flechas y Enter permiten elegir sin mouse. La tarjeta de resultados tiene ancho y márgenes amplios para facilitar su lectura en F6. Si vuelve a buscar, limpia el monto y la ficha. El monto a abonar se confirma antes de elegir medio. Para efectivo, `cobro/pagina.py` pide aparte cuánto dinero recibió el cajero y muestra en vivo cuánto falta o sobra; al abrir indica el monto pendiente y si el recibido coincide muestra vuelto $0.00. Al confirmar ese recibido pide PIN y abre el cajón solo si se autoriza. Si se cancela el PIN, conserva el recibido en pantalla y no abre el cajón. Los otros medios piden PIN antes de iniciar su motor. No abre la venta. Después, F6 y el admin confirman el abono con `cerebro.abonar_caja`. Los colores en `paleta.py`.

## Seguridad para gran empresa

- **Búsqueda por nombre limitada**: Cuando se busca por nombre, se muestran máximo 5 resultados. Si hay más, se indica al cajero que refine la búsqueda usando DNI o teléfono. Esto evita exposiciones masivas de datos en pantallas públicas.
- **Deudas ocultas en lista**: La lista de resultados no muestra montos de deuda por seguridad. Solo se revela la deuda al seleccionar un cliente específico.
- **Validación de sobreabono**: Si el cajero intenta abonar más que la deuda, aparece un diálogo de confirmación con advertencia. Esto previene errores y abusos.
- **Timer de búsqueda optimizado**: 200ms para balancear velocidad y rendimiento en bases de datos grandes.

`IMPRIMIR SALDO` saca tres números: saldo anterior, crédito y saldo. En el uso normal, al confirmar el abono sale el mismo ticket con el saldo guardado. Paso 6 F5 reutiliza la ficha con `seleccionar_cliente_directo`, oculta la búsqueda y suprime ese ticket separado: la venta fiada que continúa imprime el abono previo junto con la compra. El historial no se imprime acá.

Al volver al paso 5, el mensajero es el mismo de un cobro normal: `✅ COBRO EXITOSO — nombre · pago · saldo`, con el marco verde. Lo publica `medios/cerrar.avisar` al asentar. En Paso 6 F5, volver significa regresar a la confirmación Fiado; el abono ya está asentado y no modifica el total de la venta.
