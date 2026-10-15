# Plano Piramidal: Paso 6 (Caja y Medios de Pago)

## Filosofía
El **Paso 6** es el embudo final de toda venta. No calcula precios ni suma carritos; su única responsabilidad es **cobrar el total** y entregar un ticket.
Sigue la estructura piramidal: `paso6_cobro.py` es el Orquestador Central que recibe la orden desde el Paso 5, inyecta la interfaz del medio de pago solicitado, y cuando este grita "¡PAGADO!", se lo entrega al Motor de Pagos para asentar la venta en la base de datos.

## Estructura de Vías y Rutas

```text
src/cajero/paso6_cobro/
│
├── reparacion.md                 <-- Si se rompe velocidad/ESC/QR, este archivo manda
├── decisiones.md                 <-- F9, PIN y token: por qué aún no
├── paso6_cobro.py                <-- Orquestador de la ventana. Teclas F1–F12 e inyecta el medio.
│
├── componentes_paso6_cobro/      <-- Botones, teclado, total, selector de método.
│
├── rutas_de_cobro/
│   ├── salida/                   <-- ESC: vuelve limpio a la grilla
│   ├── efectivo/  tarjeta/  qr/  transferencia/  mixto/
│   └── fiado_piramidal/          <-- CRÉDITO y COBRANZA
│
├── fiado_en_cobro/ui/buscador_clientes/   <-- Buscador que usa el orquestador
│
└── motor_pagos/                  <-- Cierre de la venta (sin UI)
```

## Flujo del Tren (El Paso a Paso del Cobro)

1. **Entrada al Embudo:** 
   El usuario presiona `COBRAR` en el Paso 5. `paso6_cobro.py` despierta, recibe `$10.000` como `total_final`, y por defecto inyecta el panel de **Efectivo** en el medio de la pantalla.

2. **Cambio de Vías (Los F-Keys):**
   - El cajero oprime el método deseado en la botonera lateral (o con atajos de teclado F1..F6).
   - El orquestador borra el panel anterior e inyecta la ruta nueva.
   - *¿Apretó Tarjeta?* Se inyecta la ruta `tarjeta/`.
   - *¿Apretó ⚖ CRÉDITO o COBRANZA?* Se inyecta `fiado_piramidal/`. El F5 del cobro se retiró.
  - *¿Apretó ESC?* `salida/proceso.py` suelta el proceso y vuelve a la grilla. No cierra el cobro.

3. **Ejecución y Despacho:**
   - La ruta inyectada hace su trabajo. Ejemplo: en Efectivo el cliente entrega $20.000, la ruta calcula el vuelto de $10.000.
   - La ruta emite la señal `pago_listo`.
   - El Orquestador recibe el OK, toma la plata, y la empuja hacia el `motor_pagos/motor_principal.py`.

4. **El Motor de Pagos (Fondo):**
   - Este motor invisible entra a la base de datos de MaríaDB/SQLite.
   - Guarda el movimiento en la caja del cajero.
   - Resta el stock de los fideos y las cocacolas.
   - Manda el archivo binario a la Impresora de 58mm/80mm y abre el cajón de dinero.
   - Devuelve la pantalla al Paso 1, lista para el siguiente cliente.
