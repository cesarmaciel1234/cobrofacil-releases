# Plano: crédito y cobranza en el cobro

Rama: `src/cajero/paso6_cobro/rutas_de_cobro/fiado_piramidal/`

Esto es **paso 6**. F6 es tecla del paso 5: cobranza pura, sin carrito. Acá el cliente está comprando. Mismo `MotorCobranzaMedios`. Tabla: `src/cajero/README.md`.

## Frente

El cajero, en los medios de pago, toca **⚖ CRÉDITO** o **COBRANZA**. La hoja muestra el orquestador (`orquestador_credito.py`).

- **CRÉDITO:** el ticket va a la cuenta. No cobra plata ahora.
- **COBRANZA:** el cliente compra y, si quiere, paga una deuda. `mostrar(..., "MasCredito")` → buscador → `PanelCobranza`. Mismos medios que F6.
- **F6:** no está en esta hoja. Cobranza sin venta, en el paso 5.

1. **Buscador** (`fiado_en_cobro/ui/buscador_clientes/`): DNI o nombre. Un match: Enter elige. Varios: flechas o mouse y Enter. Sin match: Enter crea. En COBRANZA el título dice COBRANZA y elige cliente para liquidar.
2. **Crédito — verde** (`ruta1_margen_aprobado/`): el disponible cubre el carrito. Segundo Enter (350 ms) cierra la venta a cuenta.
3. **Crédito — rojo** (`ruta2_limite_superado/`): el carrito supera el disponible. PIN de supervisor para excepción, o Esc. No hay botón de cobranza.
4. **Cliente nuevo** (`ruta3_cliente_nuevo/`): alta exprés con límite 50.000.

El F5 del cobro se retiró. F9 sigue siendo emergencia en lienzos digitales, sin PIN, para amaestrar. No lo saques.

ESC cierra el proceso entero y vuelve a la grilla. `reiniciar` no llama al cerebro.

## Fondo

- Búsqueda: `MotorBusquedaClientes` → `cerebro.buscar`. No se lista toda la tabla `clientes` al abrir la hoja.
- Saldo y límite: `cerebro.obtener`.
- Cierre de la venta: el orquestador emite `pago_completado`; el motor real `finalizar` asienta el ticket. En COBRANZA, `PanelCobranza` asienta el abono (QR/Point/transferencia al mismo nivel que el cobro del ticket) y después se cierra el ticket.

## Qué no romper

- Clave interna de CRÉDITO: `Clientes`. `crédito` en `REGISTRO` es tarjeta de crédito.
- PIN apagado en cobranza y en F9. PIN de supervisor solo en límite superado. No lo enciendas: `paso6_cobro/decisiones.md`.
- El buscador es visual. La consulta está en el motor.
