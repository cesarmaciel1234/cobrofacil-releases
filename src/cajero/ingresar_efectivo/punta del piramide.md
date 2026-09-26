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

Abre en las tres tarjetas blancas. El gris de alrededor tapa el paso 5. El clic entra a Cambio, Fiado u Otros. Adentro, izquierda y derecha cambian de opción. Escape vuelve a las tarjetas. Escape en las tarjetas cierra. Desde admin, Abonar entra directo a Fiado y Escape cierra. Fiado, al confirmar el importe, saluda con el nombre del cliente y pregunta con qué paga. Efectivo pide el monto recibido, muestra el vuelto y abre el cajón. Transferencia escucha como el cobro (toast Asociar) y F9 registra a mano. Tarjeta y QR igual: F9 es `F9 MANUAL`. El QR se dibuja en esa hoja. La cuenta la escribe `medios/cerrar.py`. Si falla, el paso 5 avisa y la venta sigue.
