# Módulo de Cobranza y Liquidación de Cuenta

## Qué hace
Gestiona el cobro y liquidación de deudas en cuenta corriente y compras de mostrador de forma autónoma, separada del flujo tradicional de crédito. Permite ingresar montos totales o parciales, liquidar carritos o deudas previas y operar con todos los medios de pago (Efectivo, Tarjeta, QR, Transferencia y Mixto).

## Qué función cumple
- **`PanelCobranza` (`panel_cobranza.py`)**: Vista visual interactiva del centro de cobranzas.
  - `poblar(datos)`: Carga el desglose financiero con deuda anterior, compra actual y total sugerido.
  - `_iniciar_cobranza(metodo)`: Despliega el lienzo del medio seleccionado.
  - `_iniciar_cobro_mixto_secuencial(det)`: Orquesta cobros combinados ejecutando el tramo electrónico primero y el efectivo al final.
  - `procesar_f9()`: Habilita el bypass o forzado manual de contingencia electrónica.
- **`MotorCobranzaMedios`**: Asienta contablemente el ingreso en el cerebro y en la caja física sin pedir PIN.

## Cómo funciona
1. **Acceso directo**: Se accede mediante el botón **COBRANZA** de Paso 6 (o tras seleccionar un cliente para abonar).
2. **Selección de medios en pantalla**: Los botones dedicados (`Efectivo`, `Tarjeta`, `QR`, `Transf.`, `Mixto`) permiten elegir el medio sin ocupar atajos de función para no colisionar con la botonera principal del cajero (F1 ticket, F2 cerrar, F3 descuento, F4 recargo).
3. **Flujo Efectivo en 1 segundo**: Al tener el monto total sugerido en foco, presionar `[ ENTER ]` abre el lienzo de Efectivo y un segundo `[ ENTER ]` asienta el abono y abre el cajón portamonedas.
4. **Cobro Mixto Digital-Primero**: En operaciones mixtas, se cobra primero el QR/Tarjeta/Transferencia por su importe parcial; una vez aprobado, se asienta el total, se registra el efectivo en caja y se abre el cajón.

