# 🏗️ Motor Principal de Cobros (Paso 6)

## Visión Arquitectónica (Procesos y Subprocesos Piramidales)

El Motor Principal de Cobros no sabe cómo funcionan las tarjetas, ni le importa quién es el cliente del fiado. Su única responsabilidad es decirle a un **Proceso Independiente**: *"Cóbrame esto. Avísame cuando termines"*.

### La Pirámide:
```text
▲ motor_principal.py (Orquestador Supremo)
│  (Recibe la solicitud, la empaqueta en un DTO y la lanza al vacío)
│
├─► dtos/orden_cobro.py
│   (Un objeto puro y limpio. Solo contiene: Total, Carrito, Cajero. ¡Nada específico de un método!)
│
└─► procesos/ (Capa de Aislamiento Total)
    │
    ├── proceso_efectivo/
    │   ├── efectivo_main.py (Manejador)
    │   └── subprocesos/ (Cálculo de Vuelto, Gatillo Cajón Físico)
    │
    ├── proceso_qr/
    │   ├── qr_main.py (Manejador)
    │   └── subprocesos/ (API MercadoPago, Webhooks, Long Polling)
    │
    └── proceso_credito/
        ├── fiado_main.py (Manejador)
        └── subprocesos/ (Buscador de Clientes, Validar Límites, Registrar Deuda)
```

### Regla de Aislamiento Total:
- La UI (paso 6) ya **NO** debe conocer variables como `cliente_id` o `nombre_pendiente`.
- Si el método seleccionado es **Fiado**, el UI llama a `motor_principal.iniciar("Fiado", OrdenCobro)`.
- El `proceso_credito` se encargará de levantar sus propias ventanas para buscar al cliente, validar deudas, y cuando esté todo listo, guardará en la DB.
- Al final, el proceso le responde al Motor Principal: `(True, "Fiado completado")` o `(False, "Canceló")`. El Motor simplemente le avisa a la UI que muestre el ticket.
