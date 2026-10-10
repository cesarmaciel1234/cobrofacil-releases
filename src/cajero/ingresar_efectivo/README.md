# Ingreso de efectivo

El gris de atrás tapa el paso 5. La hoja clara crece con el espacio disponible del cajero (hasta 960 × 700 px), sin excederlo, y mantiene margen interior amplio alrededor del título y las tres tarjetas de alto contraste, icono, título y texto breve de ayuda. El resaltado responde al foco de teclado, no al movimiento del mouse; Tab recorre las tarjetas, las flechas cambian la selección y Enter/Espacio activa la enfocada. Los botones exponen nombre y descripción accesibles. Esc vuelve a las tarjetas. No muestra el título «INGRESO DE DINERO». Fiado, al confirmar el importe, sigue en esta ventana: el clic del medio pide el PIN y el QR se dibuja en `fiado/cobro/`. Paso 6 también puede abrir este diálogo directamente sobre el cliente seleccionado al usar F5; esa operación registra un abono previo separado y vuelve a la confirmación de venta fiada.

## Seguridad para gran empresa

El módulo Fiado incluye protecciones especiales para operar en entornos con pantallas expuestas al público:
- Búsqueda por nombre limitada a 5 resultados para evitar exposición masiva de datos
- Deudas ocultas en la lista de resultados (solo visible al seleccionar cliente)
- Validación de sobreabono con confirmación explícita
- Mensajes de UX mejorados para claridad y profesionalismo

Ver detalles en `fiado/README.md`.

La punta de esta rama es `punta del piramide.md`.
