# Plano: Proceso Piramidal de Crédito (Venta en Paso 6)

## ¿Qué es esto?
Este es el módulo que se activa en **Paso 6** cuando el cliente decide llevarse su compra anotada en cuenta corriente (Venta a Crédito / Fiado).

## Arquitectura Piramidal (Frente y Fondo)

### Frente (Componentes Modulares en `ui/` o `componentes_fiado/`)
El orquestador `panel.py` ya no es un bloque gigante. Delega sus vistas en:
1. **Buscador**: El cajero busca por nombre o DNI.
2. **Crédito Aprobado**: Panel verde de confirmación que previene dobles Enter accidentales mediante un modo de `"transicion"` ciego de 150ms.
3. **Lienzos de Pago Integrado (F5)**: Si el cliente además de llevarse fiado quiere abonar algo de la cuenta en ese momento, el sistema incrusta los selectores de Efectivo, Tarjeta, QR y Transferencia aquí mismo.

### Fondo (Motores de Base de Datos y Lógica)
- Se delegan las reglas pesadas a **Motores** (por ejemplo, `MotorBusqueda` para evaluar deudas límite, y `MotorCobranza` si el cliente abona dinero antes de cerrar).

## Flujo: Los Dos Procesos
1. **Un proceso (El Normal - Fiar y salir)**:
   - El cajero selecciona al cliente en el buscador. 
   - Apreta Enter (1ra vez). El panel cambia a `"transicion"` y luego a `"confirmando"` (Pantalla Verde de Aprobado).
   - Apreta Enter (2da vez). `panel.py` emite la señal `pago_listo` a la ventana madre `Paso6Cobro`, la cual asienta la deuda y emite el ticket fiscal o interno.

2. **Otro proceso (Pagar Saldo en Vivo - F5)**:
   - El cajero selecciona al cliente.
   - En lugar de apretar Enter, el cajero decide cobrarle un abono de la deuda vieja apretando un botón o ingresando a los medios de cobro.
   - Paga con Efectivo, Tarjeta, etc., usando los lienzos nativos (que atrapan el `F9` manual en caso de fallos del TPV).
   - Una vez asentado el pago, se vuelve a la Pantalla Verde para que la compra actual (la que está en el carrito) pase a la cuenta.
