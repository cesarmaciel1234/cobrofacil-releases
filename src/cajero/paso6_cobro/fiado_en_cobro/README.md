# Módulo de Validación de Cuenta Corriente (Fiado)

Este módulo encapsula el flujo de validación de pago mediante **Fiado / Cuenta Corriente** actuando como un validador independiente (similar a la terminal de tarjetas).

## Arquitectura (Enterprise)
Anteriormente, el cobro por fiado formaba parte integral del controlador central (`paso6_cobro.py`) y carecía de un paso explícito de confirmación visual (el sistema cerraba la venta tan pronto se hacía clic en el cliente).

Con esta refactorización, el validador actúa como una "Caja Negra" conectable (Plug & Play):
1. **El Motor Central** invoca `panel_fiado.mostrar(monto)`.
2. **El Validador** busca al cliente, verifica los límites, autoriza (o pide PIN) usando la lógica de `HojaCuentaCobro`.
3. **El Validador frena el flujo**, y en un panel completo muestra la aprobación con los detalles de la compra, límite disponible, y solicita un **ENTER final** al cajero.
4. Una vez confirmado, el Validador emite `pago_listo.emit(cliente_id)`.

## Ventajas del Patrón
- La caja nunca se cierra accidentalmente al equivocarse de clic (se requiere una acción consciente y doble validación).
- Se reutiliza idéntico para cobros **Directos** o cobros **Mixtos** sin tener que duplicar el código.
- Da una impresión visual de nivel corporativo al cajero (gran cartel verde tipo terminal).
