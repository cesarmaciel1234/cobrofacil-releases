# Punta de la pirámide — ingreso de dinero

Cambio, fiado y otros. Esta carpeta los junta. No cobra la venta.

```
ingresar_efectivo/
  punta del piramide.md
  dialogo.py               la ventana (opciones → formulario → cobro)
  opciones/                Cambio, Fiado, Otros
  cambio/                  fondo fijo
  fiado/                   el cliente y el abono
    cobro/                 PIN, medios, QR/Point/transferencia
  otros/                   un ingreso con descripción
  pie/                     cancelar y confirmar
```

Abre en las tres tarjetas claras sobre el gris que tapa el paso 5. La hoja crece según el espacio del cajero, con máximo de 960 × 700 px, y mantiene sus márgenes internos. El selector presenta el nombre del centro, una pregunta guía y tarjetas con icono, acción y color propio; el resaltado marcado responde solo al foco de teclado, nunca al movimiento del mouse. Tab recorre las tarjetas, las flechas izquierda/derecha o arriba/abajo cambian la selección y Enter/Espacio activa. Desde admin, Abonar entra directo a Fiado y Escape cierra. En Fiado, el monto a abonar ya se ingresó antes de elegir el medio. En efectivo, se ingresa aparte cuánto dinero recibió el cajero y se ve el vuelto; solo al confirmar se solicita PIN y, si se autoriza, abre el cajón y registra el abono. Si el PIN se cancela, mantiene el recibido y no abre el cajón. En Mixto, espera que terminen los medios electrónicos antes de abrir el cajón. Transferencia escucha como el cobro (toast Asociar) y F9 registra a mano. Tarjeta y QR igual: F9 es `F9 MANUAL`. El QR se dibuja en esa hoja. La cuenta la escribe `medios/cerrar.py`. Si falla, el paso 5 avisa y la venta sigue.
