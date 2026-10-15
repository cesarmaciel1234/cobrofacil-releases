# Botones de Acción

## Qué hace
Agrupa la grilla de botones de acción de la botonera lateral derecha del proceso de cobro (F1 Imprime, F2 Sin ticket, F3 Redondeo, F4 Recargo, F7 Último monto, F11 Point MP, F12 Verif QR).

## Qué función cumple
- **`PanelBotonesAccion` (`panel_botones_accion.py`)**: Utiliza `QStackedWidget` (`pila_f2`, `pila_point`, `pila_extra`) para alternar contextualmente los botones según el medio de pago seleccionado (Efectivo, Tarjeta, QR, Transferencia, Mixto, Crédito/Cobranza).
- Mantiene preservada la cuadrícula dimensional sin colapsar el layout.
- El botón F5 ("pagar cuenta") se retiró. Cobranza es el medio `MasCredito`. F5 de la venta es retiro de caja.

## Regla: ninguna tecla F se repite
Cada tecla hace **una sola cosa** y aparece **una sola vez** en pantalla:
- **F12 = Verif QR** (solo QR y Mixto). `paso6_cobro._tecla_f12`.
- **F7 = Último monto** (solo Transferencia y Mixto). `paso6_cobro._tecla_f7`.
Antes, en Mixto se veían dos botones "F12" a la vez y la tecla adivinaba cuál usar. No volver a reutilizar una F.

## Cómo funciona
- Columna 1: F1 Imprime (arriba) y F4 Recargo (abajo).
- Columna 2: F2 Sin ticket / F7 Último monto en Mixto (arriba) y F11 Point MP / Hueco (abajo).
- Columna 3: F3 Redondeo (arriba) y F12 Verif QR / F7 Último monto en Transferencia / Hueco (abajo).
- Dentro de Cobranza se usa el submedio activo (`_submetodo_cobranza`): QR → F12, Tarjeta → F11, Transferencia → F7.
