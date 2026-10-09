# Plano del Constructor de Ticket de Venta

## Frente (Usuario)
El sistema genera un ticket en papel (físico) al finalizar una venta desde el Cajero. El usuario no interactúa con una ventana aquí, sino con el resultado impreso de su operación.

## Fondo (Sistema)
La orquestación ocurre en `ConstructorTicketVenta.construir()`. Este une los sub-bloques en un solo `bytearray` de comandos ESC/POS.
- `printer.py` (función `imprimir_ticket_venta`) llama al constructor y envía los bytes a la cola de impresión (`_send_raw_data`).
- Submódulos (cada uno devuelve un fragmento de bytes):
  - `encabezado`: Reseteo de impresora, logo/nombre local, datos de cabecera AFIP o interno.
  - `cuerpo_productos`: Iteración de items, cálculo de formato y alineación de columnas.
  - `totales_vuelto`: Totales, descuentos, cálculo de IVA, y desglose de pagos.
  - `pie_condiciones`: Mensajes finales, saldos de cuenta corriente, código QR AFIP, corte de papel y orden de apertura del cajón portamonedas.

## Novedades
- Soporta Impresoras de 58mm (32 caracteres) y 80mm (48 caracteres) din�micamente configurables.
