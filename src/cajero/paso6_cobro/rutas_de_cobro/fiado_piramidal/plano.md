# Plano de Arquitectura Piramidal: Cobro a Fiado y Centro de Cobranza

## Visión General
Este módulo procesa las operaciones de cuenta corriente y cobranza en el TPV de mostrador (Paso 6):
1. **⚖ CRÉDITO (`Fiado` / `Clientes`)**: Carga compras a la cuenta corriente del cliente evaluando su margen en tiempo real.
2. **COBRANZA (`MasCredito`)**: Permite abonar o liquidar saldo deudor y cobrar la venta en curso en una sola transacción integrada.

El diseño sigue el principio de **semáforo de privacidad y velocidad de mostrador**: sin mostrar datos financieros a la fila, con validación inmediata y máxima agilidad de teclado.

---

## Arquitectura Frente y Fondo

### Frente (`orquestador_credito.py`)
Controlador orquestador (`QStackedWidget`) que gobierna las vistas:
- **`via_buscador`**: Búsqueda ultrarrápida de clientes por Nombre o DNI con autocompletado en vivo.
- **`via_aprobado` (Ruta 1)**: Pantalla verde de confirmación cuando el disponible cubre el carrito.
- **`via_bloqueo` (Ruta 2)**: Pantalla de aviso cuando el límite es superado, con acceso a desbloqueo por PIN supervisor o derivación a Cobranza.
- **`via_cobranza` (`modulo_cobranza/panel_cobranza.py`)**: Módulo independiente de liquidación y cobranza con desglose financiero y pastillas rápidas.
- **`via_nuevo` (Ruta 3)**: Alta exprés de clientes sin abandonar el flujo de cobro.

### Fondo (Cerebro Contable & Motor de Cobranzas)
- **`src/clientes_fiado/cerebro/cerebro.py`**: Impacto de saldos, cuentas corrientes y auditoría.
- **`MotorCobranzaMedios`**: Motor empresarial que asienta el ingreso según el medio (Efectivo, Tarjeta, QR, Transferencia, Mixto) y registra entradas de efectivo en caja.

---

## Flujos Operativos

```
                              [ Paso 6: Selección ]
                                  /            \
                       [ ⚖ CRÉDITO ]        [ COBRANZA ]
                             │                   │
                             ▼                   ▼
                     [ Buscador ]          [ Buscador ]
                             │                   │
                     Evalúa Disponible           ▼
                      /            \      [ Módulo Cobranza ]
             (Alcanza)              (Excede)     │
                 ▼                      ▼        ├── 1: Efectivo (Sin PIN, abre cajón)
          [ Verde: Aprobado ]    [ Bloqueo ]    ├── 2: Tarjeta (Point terminal)
                 │                      │        ├── 3: QR (Mercado Pago dinámico)
                 ▼                      ▼        ├── 4: Transferencia
             [ ENTER ]            [ Cobranza/PIN ] └── 5: Mixto (Digital-Primero)
                 │                      │                │
                 └──────────────┬───────┘                ▼
                                ▼              [ 1° Digital (QR/Tarj/Transf) ]
                        [ Cierre de Venta ]              ▼
                                                [ 2° Abre Cajón (Efectivo) ]
```

### Proceso 1: Crédito Normal (Margen Aprobado)
1. Selección de cliente en el buscador interactivo.
2. Si `(limite - deuda) >= carrito`, se presenta la pantalla Verde.
3. Segundo `[ ENTER ]` (con debounce anti-rebote de 250ms) asienta la venta y emite el ticket.

### Proceso 2: Cobranza Directa (`MasCredito`)
1. Clic en **COBRANZA** (o tecla directa) en Paso 6.
2. Selección del cliente $\rightarrow$ entra directo a `PanelCobranza` (`modulo_cobranza/`).
3. Ofrece opciones inmediatas: `Solo Carrito`, `Solo Deuda`, `Liquidar Todo` o importe libre.
4. **Sin solicitud de PIN**: Se cobra ágilmente sin trabar al cajero con claves repetidas.
5. Emite ticket con `SALDO PREVIO`, `ABONO COBRANZA` y `SALDO RESTANTE`.

### Proceso 3: Cobro Mixto Digital-Primero
Cuando se reparte el pago mixto (por ejemplo: Efectivo + QR):
1. El cajero ingresa los montos en `LienzoMixto` (navegación rápida con ENTER entre campos).
2. Al confirmar, **primero se ejecuta el medio digital**: se despliega el QR o la terminal por el importe electrónico.
3. El cliente abona o el cajero activa **F9 Emergencia**.
4. Una vez aprobado el medio digital, el sistema asienta el total, registra el efectivo en caja y **abre el cajón portamonedas**.
5. Emite ticket y finaliza la venta.

---

## Atajos y Aislamiento de Teclado
- **ENTER Instantáneo**: Al ingresar a Cobranza con el importe total sugerido preseleccionado, presionar `[ ENTER ]` inicia de inmediato el cobro en Efectivo. Un segundo `[ ENTER ]` en el lienzo confirma la operación en menos de 1 segundo.
- **Respeto a la Botonera Principal**: No se asignan teclas F1 a F5 a los medios de pago dentro de Cobranza para evitar colisionar con la botonera global del cajero (F1 ticket, F2 cerrar, F3 descuento, F4 recargo). La selección se realiza con clic táctil o directo sobre los botones.
- **Navegación en Cobro Mixto**: Al presionar `[ ENTER ]` en un casillero, el remanente se autocompleta automáticamente en el siguiente campo; al cubrir el 100%, presionar `[ ENTER ]` confirma al instante.
- **F9 Emergencia**: Activo tanto por tecla como por botón en pantalla para saltar esperas de QR/Point en caso de contingencia.
- **ESC**: Vuelve al paso inmediatamente anterior o cancela ordenadamente hacia la selección de métodos.


