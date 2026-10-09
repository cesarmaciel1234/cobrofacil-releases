# Plano: Proceso Piramidal de Crédito (Fiado en Cobro)

Frente:
- **Un proceso: el normal:** El cajero entra a Fiado (F6), selecciona al cliente, presiona Enter para confirmar. El panel se pone verde indicando que el crédito está aprobado. Al presionar Enter de nuevo, se carga la venta a la cuenta corriente del cliente y se sale (imprimiendo el ticket de fiado).
- **Otro proceso: F5 (Cobro Integrado):** Si el cliente quiere pagar saldo en vivo, el cajero presiona F5 estando en el panel de Fiado. El panel verde se transforma en un selector de cobranza, mostrando métodos de pago (Efectivo, Tarjeta, etc.). Al elegir uno, el lienzo nativo de cobro se embebe en el panel. El cliente paga (abono) y luego se carga la venta actual a la cuenta.

Fondo:
- El módulo está estructurado en pirámide (modularizado en `componentes_fiado/`):
  - `PanelFiadoCobro` (`panel.py`) es el orquestador principal.
  - `estado_credito/`: Maneja los componentes visuales de aprobación (etiquetas y montos).
  - `selector_cobranza/`: Mantiene los botones y el stack de lienzos de pago (QR, Tarjeta, etc.).
  - `motor/`: Contiene la lógica transaccional de cobro (`MotorCobranza`).
- **Proceso Normal:** `panel.py` usa `HojaCuentaCobro` para buscar, luego muestra `estado_credito`. El Enter final emite `pago_listo`.
- **Proceso F5:** `panel.py` muestra `selector_cobranza` y sus lienzos. Al finalizar el pago en el lienzo, `MotorCobranza` asienta el pago (generando saldo a favor temporal) y luego emite `pago_listo` para que el sistema superior (`Paso6Cobro`) finalice la venta, absorbiendo ese saldo.