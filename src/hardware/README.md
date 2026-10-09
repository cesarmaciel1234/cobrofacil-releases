# Hardware - Gestión de Impresoras y Periféricos

Este directorio contiene los módulos para gestionar el hardware de impresión, cajones de dinero y alarmas de seguridad.

## Módulos

### `printer.py`
**Responsabilidad**: Gestión de impresoras térmicas ESC/POS y cajones de dinero.

Clase principal: `PosPrinter`

Funciones principales:
- `imprimir_ticket_venta(...)`: Imprime ticket de venta con items
- `imprimir_ticket_z(...)`: Imprime reporte de cierre de caja (usa ticket_z.py)
- `imprimir_movimiento_caja(...)`: Imprime comprobante de ingreso/egreso
- `imprimir_ticket_saldos_compra(...)`: Ticket de cuenta corriente
- `imprimir_saldo_fiado(...)`: Ticket de saldo de fiado
- `abrir_cajon(...)`: Apertura del cajón de dinero
- `cortar_papel(...)`: Corte de papel
- `pitido(...)`: Sonido de la impresora
- `verificar_estado()`: Verifica conexión con impresora

Modos de conexión:
- **Windows Spooler**: Para impresoras USB/red en Windows (win32print)
- **Serial Directo**: Para impresoras en puerto COM (pyserial)
- **Simulación**: Cuando no hay impresora configurada

### `ticket_z.py`
**Responsabilidad**: Formateo del ticket de cierre de caja (Reporte Z/X).

Funciones principales:
- `formatear_ticket_z(usuario, fisico, dif, datos_z)`: Genera contenido ESC/POS del ticket
- `_formatear_moneda(valor)`: Formatea valor como moneda Argentina
- `_obtener_linea_metodo_pago(nombre, valor, indent)`: Genera línea alineada

Secciones del ticket:
1. Header (tipo de cierre, fecha, cajero)
2. Turno Cajero (fondo inicial)
3. Métodos de Pago (efectivo, tarjeta, transferencia, QR, crédito)
4. Abonos de Clientes (desglosado por método)
5. Movimientos Manuales (ingresos/egresos)
6. Global del Día (solo en modo Z)
7. Cuadre Físico (esperado vs contado)
8. Diferencia del Mes
9. Diferencia Histórica

Comandos ESC/POS utilizados:
- `ESC @`: Reset impresora
- `ESC a 1`: Alineación centro
- `ESC a 0`: Alineación izquierda
- `ESC E 1`: Negrita ON
- `ESC E 0`: Negrita OFF
- `GS V 41 00`: Corte de papel

### `cash_drawer.py`
**Responsabilidad**: Gestión centralizada del cajón de dinero (apertura, sensado, seguridad).

Clase principal: `CashDrawerManager`

Funciones principales:
- `abrir(autorizada=True)`: Envía señal física de apertura
- `set_authorized(status)`: Marca la próxima apertura como autorizada
- `check_status()`: Consulta estado físico del cajón
- `is_open`: Propiedad que indica si está abierto
- `is_authorized`: Propiedad que indica si la apertura fue autorizada

Señales:
- `drawer_opened`: Se emite cuando el cajón se abre
- `drawer_closed`: Se emite cuando el cajón se cierra
- `intrusion_detected`: Se emite cuando se abre sin autorización (llave)

Modos de conexión:
- **OPOS**: Driver OPOS para hardware 3nstar/Epson
- **ESC/POS**: Vía impresora térmica (fallback)
- **Sensor magnético**: Detección de estado físico

### `alarma_intrusion.py`
**Responsabilidad**: Toast de alarma visual cuando el cajón se abre con la llave (sin autorización).

Funciones principales:
- `mostrar_alarma_intrusion(duracion_ms=5000)`: Muestra el toast flotante
- `ocultar_alarma_intrusion()`: Oculta el toast si está visible
- `limpiar()`: Limpia la instancia singleton

Características:
- Corre por encima de todas las ventanas (WindowStaysOnTopHint)
- No captura el foco (WA_ShowWithoutActivating)
- No interfiere con el cajero
- Si falla, el sistema sigue funcionando normalmente

Véase `README_alarma_intrusion.md` para más detalles.

## Flujo de Impresión

```
UI (cierre_main_ui.py)
    ↓
_imprimir_reporte()
    ↓
printer_manager.imprimir_ticket_z()
    ↓
ticket_z.formatear_ticket_z()
    ↓
Genera bytes ESC/POS
    ↓
printer._send_raw_data()
    ↓
┌─────────────────────┐
│ Si puerto COM:      │
│   pyserial.Serial   │
├─────────────────────┤
│ Si nombre de        │
│ impresora Windows:  │
│   win32print        │
└─────────────────────┘
    ↓
Impresora térmica
```

## Configuración

En `config.json`:
```json
{
  "ticket_printer": "EPSON_TM-T20II",
  "ticket_printer_2": "Star_SP700",
  "printer_name": "EPSON_TM-T20II",
  "drawer_kick_pin": 0,
  "printer_3nstar_mode": false,
  "business_name": "MI EMPRESA",
  "business_cuit": "CUIT: 00-00000000-0",
  "business_address": "Dirección Local"
}
```

## Tipos de Cierre

El ticket muestra diferentes textos según el origen:

1. **Desde paso5 (cajero)**: `"cierre diario automatico"`
   - Detectado por `is_terminal=True` o `modo_vista="cajero"`

2. **Cierre programado 00hs**: `"cierre diario automatico"`
   - Detectado por `es_automatico=True`
   - Llamado desde sistema de tareas programadas

3. **Manual desde admin/jefe**: `"IMPRESO MANUAL"`
   - Clic en botón de imprimir desde UI de admin/jefe

## Diferencias Acumuladas

Cálculo de diferencias:
- **Diferencia del mes**: Suma de todas las diferencias desde el 1° del mes actual
- **Diferencia histórica**: Suma de todas las diferencias desde el inicio del sistema

Formato en observaciones de cierre:
```
"Cierre TURNO. Esperado: 1000.00. Dif: 50.00. Total ventas: 5000.00"
```

El módulo `diferencias.py` extrae el valor de "Dif:" usando regex y acumula.

## Codificación

- **Texto**: CP850 (Latin-1, compatible con la mayoría de impresoras térmicas)
- **Fallo**: `errors='replace'` para caracteres no soportados

## Troubleshooting

**Impresora no responde**:
1. Verificar que el nombre de impresora en `config.json` coincida con el de Windows
2. Para COM: Verificar puerto correcto (COM1, COM2, etc.)
3. Verificar que la impresora esté encendida y con papel

**Cajón no abre**:
1. Verificar configuración `drawer_kick_pin` (0=Pin 2, 1=Pin 5)
2. Algunas impresoras requieren `printer_3nstar_mode=True`
3. Verificar conexión física del cable del cajón

**Texto ilegible**:
1. La impresora debe soportar codificación CP850
2. Caracteres especiales pueden reemplazarse con `?`

## Dependencias

Librerías:
- `win32print` (opcional): Para impresoras en Windows
- `pyserial` (opcional): Para impresoras en puerto COM
- `config`: Configuración del sistema

## Notas

- El módulo `printer.py` es una fachada que delega a `ticket_z.py` para el formateo
- Esto permite mantener separada la lógica de impresión del formateo
- Facilita testing y mantenimiento del código
