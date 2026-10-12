# Plano Piramidal: F6 (Centro de Cobranzas Autónomo)

## Filosofía
El Centro de Cobranzas (F6) es una aplicación independiente dentro del TPV. No vende productos; **exclusivamente gestiona deudas y dinero a favor**.
Siguiendo la ley de rutas aisladas, F6 ya no mezcla la lógica visual en un solo archivo, sino que el orquestador (`panel.py`) desvía el tren a módulos cerrados según lo que el cajero quiera hacer.

## Estructura de Rutas

```text
src/cajero/f6_centro_cobranzas/
│
├── panel.py                      <-- El Orquestador F6. Actúa como estación central de trenes.
│
├── rutas_f6/                     <-- Las vías físicas aisladas
│   │
│   ├── 1_buscador_global/        <-- (Actualmente: ui_buscador)
│   │   ├── panel_buscador.py     (Busca al cliente)
│   │   └── README.md             (Emite el DNI/Nombre al orquestador)
│   │
│   ├── 2_analisis_cuenta/        <-- (Actualmente: ui_estado)
│   │   ├── panel_estado.py       (Recibe la info del motor. Calcula si es DEUDA o SALDO A FAVOR)
│   │   └── README.md             (Si es saldo a favor -> Pinta Verde. Si es deuda -> Pinta Rojo)
│   │
│   └── 3_ejecucion_pago/         <-- (Actualmente: ui_selector)
│       ├── panel_selector.py     (El usuario tipeó el monto y eligió Efectivo/QR)
│       ├── lienzos_embebidos/    (Muestra la tarjeta o el código QR)
│       └── README.md             (Da el OK final al Motor Global)
│
└── Motores Globales Usados:
    - MotorBusquedaClientes (Extrae la deuda y el límite)
    - MotorCobranzaMedios (Asienta el ingreso de dinero en la caja y resta la deuda)
```

## Flujo del Tren (Paso a Paso F6)

1. **Vía 1 (Buscando):**
   - El cajero oprime F6 en el panel principal.
   - El orquestador inyecta `1_buscador_global`.
   - Si no hay coincidencias, aparece el cartel `"No hay coincidencia..."` (y se puede crear un cliente nuevo con ENTER).

2. **Vía 2 (Análisis):**
   - Se selecciona a un cliente. El orquestador invoca al *MotorBusquedaClientes* y extrae la variable `deuda`.
   - Se inyecta la ruta `2_analisis_cuenta`. 
   - El módulo decide: ¿Es un saldo negativo? Muestra **Saldo a favor ($ verde)**. ¿Es un saldo positivo? Muestra **Deuda actual ($ rojo)**.

3. **Vía 3 (Cobro o Recarga):**
   - El cajero oprime "PAGAR/ABONAR".
   - Se inyecta la ruta `3_ejecucion_pago`.
   - El cajero ingresa el monto (ej: $15.000) y elige el método (Ej: Transferencia).
   - El lienzo emite un `"AUTORIZADO"`.
   - El Orquestador manda esos $15.000 al *MotorCobranzaMedios*. La caja del día suma $15.000 y el cliente descuenta su deuda. Todo de forma transparente y sin entorpecer el proceso de ventas del Paso 6.

