# Lienzo de Pago Mixto

## Qué hace
Permite distribuir el cobro de una transacción entre múltiples medios: Efectivo, Tarjeta, Transferencia y QR.

## Funciones principales
- `vaciar()`: Casilleros en cero.
- `arrancar(monto)`: Vacía, carga el total y enfoca efectivo.
- `_on_enter_campo(campo)`: Cubierto confirma. Si falta y hay menos de dos medios, completa el siguiente.
- `_validar_cobertura()`: Exacto, máximo dos medios, sin excedente digital.
- `tecla(k)`: Atiende `ENTER` para confirmar o `ESC` para volver al selector de medios.

## Cómo funciona
Solo dos medios. Esc / `vaciar` deja los casilleros en cero. Devuelve `{"Efectivo", "Tarjeta", "Transferencia", "QR"}` por `listo`. F6 encadena Tarjeta → Transferencia → QR y asienta una vez. El mixto de una **venta** vive en `paso6_cobro/mixto_en_cobro/` (puede ir resto a cliente). Este lienzo es cobranza.
