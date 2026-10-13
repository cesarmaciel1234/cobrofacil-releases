# Plano: crédito y cobranza en el cobro

Rama: `src/cajero/paso6_cobro/rutas_de_cobro/fiado_piramidal/`

## Frente

El cajero, en Paso 6, toca **⚖ CRÉDITO** o **COBRANZA**. La hoja del cobro muestra el orquestador (`orquestador_credito.py`).

1. **Buscador** (`fiado_en_cobro/ui/buscador_clientes/`): DNI o nombre. Un match: Enter elige. Varios: flechas o mouse y Enter. Sin match: Enter crea.
2. **Crédito — verde** (`ruta1_margen_aprobado/`): el disponible cubre el carrito. Segundo Enter (350 ms) cierra la venta a cuenta.
3. **Crédito — rojo** (`ruta2_limite_superado/`): el carrito supera el disponible. PIN de supervisor para excepción, o botón **COBRANZA** para abonar.
4. **Cobranza** (`modulo_cobranza/`): pastillas Solo Carrito / Solo Deuda / Liquidar Todo, monto editable, medios Efectivo / Tarjeta / QR / Transferencia / Mixto. El importe por defecto es el ticket. Saldo a favor no se cobra. Sin PIN (aún: `decisiones.md`).
5. **Cliente nuevo** (`ruta3_cliente_nuevo/`): alta exprés con límite 50.000.

F5 no abre cobranza. F9 sigue siendo emergencia en lienzos digitales, sin PIN, para amaestrar. No lo saques.

ESC cierra el proceso entero y vuelve a la grilla. `reiniciar` no llama al cerebro.

## Fondo

- Búsqueda: `MotorBusquedaClientes` → `cerebro.buscar`. No se lista toda la tabla `clientes` al abrir la hoja.
- Saldo y límite: `cerebro.obtener`.
- Abono: `MotorCobranzaMedios.finalizar` (intermediario) → `medios/cerrar.asentar` y, si entra efectivo, `MovimientosCajaService`.
- Cierre de la venta: el orquestador emite `pago_completado`; el motor real `finalizar` asienta el ticket. PIN de cobranza después (`decisiones.md`).

## Qué no romper

- Clave interna de CRÉDITO: `Clientes`. `crédito` en `REGISTRO` es tarjeta de crédito.
- PIN apagado en cobranza y en F9. PIN de supervisor solo en límite superado. No lo enciendas: `paso6_cobro/decisiones.md`.
- El buscador es visual. La consulta está en el motor.
