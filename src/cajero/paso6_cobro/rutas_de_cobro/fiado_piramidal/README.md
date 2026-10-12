# Fiado Piramidal y Cobranza

## Qué hace
Orquesta el ciclo de vida del crédito y cobranza de clientes en el punto de cobro (Paso 6): búsqueda, evaluación de saldo disponible, liquidación en vivo de deudas mediante el Módulo de Cobranza, y alta exprés de cuentas.

## Funciones principales
- `mostrar(monto, modo)`: Inicia el flujo según el modo (`Fiado`, `Clientes` o `MasCredito`).
- `_evaluar_cliente(cliente_id)`: Consulta saldo y límite en el cerebro contable y decide la ruta visual.
- `procesar_f9()`: Enruta la tecla o botón de emergencia hacia los lienzos digitales activos.
- `_finalizar_desde_cobranza()`: Concede excepción de crédito activa y cierra la venta sin duplicar autorizaciones.

## Cómo funciona
Usa un `QStackedWidget` con 5 pantallas conectadas por señales Qt:
1. `via_buscador`: Búsqueda reactiva con `MotorBusquedaClientes`.
2. `via_aprobado`: Ruta verde cuando el límite cubre la compra.
3. `via_bloqueo`: Ruta roja cuando la cuenta supera el disponible.
4. `via_nuevo`: Diálogo de creación rápida de nuevos clientes.
5. `via_cobranza`: Centro de cobranza independiente para liquidación total o parcial con todos los medios de pago.

