# Plano Piramidal: Paso 6 (Caja y Medios de Pago)

## Filosofía
El **Paso 6** es el embudo final de toda venta. No calcula precios ni suma carritos; su única responsabilidad es **cobrar el total** y entregar un ticket.
Sigue la estructura piramidal: `paso6_cobro.py` es el Orquestador Central que recibe la orden desde el Paso 5, inyecta la interfaz del medio de pago solicitado, y cuando este grita "¡PAGADO!", se lo entrega al Motor de Pagos para asentar la venta en la base de datos.

## Estructura de Vías y Rutas

```text
src/cajero/paso6_cobro/
│
├── paso6_cobro.py                <-- El Gran Orquestador. Solo sabe escuchar la tecla (F1, F2, F3...) e inyectar el módulo correcto.
│
├── componentes/                  <-- Los bloques visuales compartidos (botones laterales de la UI, teclado numérico en pantalla, total a pagar).
│
├── rutas_de_cobro/               <-- Cada medio de pago es una VÍA AISLADA:
│   │
│   ├── efectivo/                 (Panel de billetes rápidos, calcula vuelto matemáticamente)
│   ├── tarjeta/                  (Input para N° de comprobante / lote)
│   ├── qr_y_transferencia/       (Módulos ligeros para pagos digitales)
│   ├── mixto/                    (Calculadora para dividir pagos: Mitad efectivo, mitad tarjeta)
│   │
│   └── fiado_piramidal/          <-- La super-ruta aislada de Créditos (F5)
│       ├── orquestador_credito.py
│       ├── 1_margen_aprobado/    (Ruta Verde: Confirmación rápida)
│       ├── 2_limite_superado/    (Ruta Roja: Pide PIN de Admin)
│       └── 3_cliente_nuevo/      (Ruta Azul: Crear expediente)
│
└── motor_pagos/                  <-- El Cierre Definitivo (Sin interfaz visual)
    ├── motor_principal.py        (Orquestador de base de datos)
    ├── asentar_caja/             (Guarda los billetes en la caja de este turno)
    ├── descontar_stock/          (Da de baja los productos del inventario)
    └── generar_ticket/           (Envía la orden cruda a la impresora térmica)
```

## Flujo del Tren (El Paso a Paso del Cobro)

1. **Entrada al Embudo:** 
   El usuario presiona `COBRAR` en el Paso 5. `paso6_cobro.py` despierta, recibe `$10.000` como `total_final`, y por defecto inyecta el panel de **Efectivo** en el medio de la pantalla.

2. **Cambio de Vías (Los F-Keys):**
   - El cajero oprime el método deseado en la botonera lateral (o con atajos de teclado F1..F6).
   - El orquestador borra el panel anterior e inyecta la ruta nueva.
   - *¿Apretó Tarjeta?* Se inyecta la ruta `tarjeta/`.
   - *¿Apretó Crédito?* Se inyecta la `fiado_piramidal/` que hace su propio proceso independiente de buscar cliente y evaluar límites.

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
