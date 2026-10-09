# Cierre de Caja (Cerebro Global)

Sistema completo de cierre de caja para TPV PRO 2026, implementando Reporte Z/X con control de efectivo, métodos de pago y diferencias acumuladas.

## Arquitectura

```
cerebro_global/
└── cierre_caja_cerebro/
    ├── motor_cierre.py              # Fachada pública (API)
    ├── procesos/                    # Lógica de negocio
    │   ├── totales.py              # Cálculo de totales de ventas
    │   ├── diferencias.py          # Cálculo de diferencias acumuladas
    │   ├── cierre.py               # Ejecución del cierre
    │   ├── esperado.py             # Cálculo de efectivo esperado
    │   ├── modos.py                # Normalización de modos
    │   ├── historial_cortes.py     # Consulta de cortes realizados
    │   └── multi_caja.py           # Gestión multi-caja
    └── README.md                   # Este archivo
```

## Fachada Pública: `motor_cierre.py`

Clase `MotorCierre` que expone la API pública del sistema de cierre.

Métodos estáticos:

```python
# Obtener datos para el panel de cierre
MotorCierre.obtener_datos_cierre_diario(fecha_str, cajero, caja_id)
    → Dict con totales, abonos, movimientos, diferencias

# Cerrar caja (ejecutar corte Z/X)
MotorCierre.cerrar_caja(username, caja_id, fisico, dif, esperado, t_total, modo)
    → True si exitoso, False si falla

# Consultar cortes ya realizados
MotorCierre.listar_cortes_del_dia(fecha_str, caja_id, cajero)
    → List[Dict] con información de cada corte

# Resumen por cajero
MotorCierre.resumen_cortes_por_cajero(fecha_str, caja_id)
    → Dict resumido por cajero

# Gestión multi-caja
MotorCierre.listar_cajas()
    → List[int] con IDs de cajas configuradas

MotorCierre.resumen_tienda(fecha_str)
    → Dict con consolidado de todas las cajas
```

## Flujo Completo de Cierre

### 1. Panel de Cierre (UI)

```python
# UI muestra métricas del turno
datos = MotorCierre.obtener_datos_cierre_diario(
    fecha_str="2026-10-04",
    cajero="juan",
    caja_id=1
)

# Datos devueltos:
{
    "fondo": 500.0,
    "v_efectivo": 1250.0,
    "v_tarjeta": 800.0,
    "v_trans": 150.0,
    "v_credito": 500.0,
    "v_totales": 2200.0,
    "v_caja_total": 1850.0,  # Esperado para arqueo
    "abonos_efectivo_detalle": 500.0,
    "abonos_transferencia": 100.0,
    "abonos_digital": 350.0,
    "entradas_efectivo": 200.0,
    "salidas_efectivo": 50.0,
    "diferencia_mes": 150.0,
    "diferencia_historica": -250.0
}
```

### 2. Arqueo de Caja

El cajero cuenta el efectivo físico y lo ingresa en el panel de arqueo.

### 3. Ejecución del Cierre

```python
# Usuario confirma cierre
exito = MotorCierre.cerrar_caja(
    username="juan",
    caja_id=1,
    fisico=1850.0,        # Efectivo contado
    dif=0.0,              # Diferencia (físico - esperado)
    esperado=1850.0,      # Efectivo esperado
    t_total=2200.0,       # Total ventas
    modo="cajero"         # "cajero" o "dia"
)
```

**Lógica interna**:
1. Valida que la caja no esté ya cerrada
2. Registra movimiento de caja tipo 'CIERRE_TURNO' o 'CIERRE_Z'
3. Actualiza estado de ventas a 'CERRADA'
4. Retorna True si exitoso

### 4. Impresión del Ticket

```python
# Generar ticket
datos_z = {
    "fondo": 500.0,
    "turno_efectivo": 1250.0,
    "turno_tarjeta": 800.0,
    "turno_credito": 500.0,
    "turno_total": 2200.0,
    "efectivo_esperado": 1850.0,
    "es_automatico": False,
    "es_cajero": True,
    "diferencia_mes": 150.0,
    "diferencia_historica": -250.0,
    # ... más datos
}

printer_manager.imprimir_ticket_z(usuario, fisico, dif, datos_z)
```

## Modos de Cierre

### Modo Cajero (Cierre X)
- **Uso**: Cierre de turno individual de un cajero
- **Alcance**: Solo ventas del cajero desde su última apertura
- **Tipo movimiento**: 'CIERRE_TURNO'
- **Ticket**: "REPORTE DE TURNO - CIERRE DE CAJA"

### Modo Día (Cierre Z)
- **Uso**: Cierre global del día para una caja específica
- **Alcance**: Todas las ventas del día en esa caja
- **Tipo movimiento**: 'CIERRE_Z'
- **Ticket**: "REPORTE Z - CIERRE DE CAJA"

### Modo Multi-Caja
- **Uso**: Consolidado de todas las cajas (modo cadena/franquicia)
- **Alcance**: Suma de todas las cajas
- **Solo lectura**: No permite arqueo/corte directo
- **Requisito**: Seleccionar caja específica para cortar

## Métodos de Pago

Sistema clasifica pagos en:

**Efectivo**:
- 'Efectivo'
- 'Mixto' (parte efectivo)
- Cualquier método con '%EFECTIVO%'

**Digital**:
- 'Tarjeta', 'Crédito', 'Débito'
- 'Transferencia', 'Transf.'
- 'QR', 'Digital', 'MercadoPago'
- 'Vales' (despensa)
- 'Cheques'

**Crédito**:
- 'Fiado' (cuenta corriente)

## Abonos de Clientes

Los abonos a cuenta corriente se registran como movimientos de caja tipo 'INGRESO' con observaciones como:
- "Pago de clientes - Juan Perez - Transferencia"
- "Pago de clientes - Maria Garcia - Efectivo"
- "Pago de clientes - Carlos Lopez - QR MercadoPago"

El sistema desglosa estos abonos por método de pago en el ticket Z.

## Diferencias Acumuladas

### Cálculo

1. **Diferencia del mes**: Suma de todas las diferencias desde el 1° del mes actual
2. **Diferencia histórica**: Suma de todas las diferencias desde el inicio del sistema

### Extracción

Las diferencias se almacenan en las observaciones de los movimientos de cierre:
```
"Cierre TURNO. Esperado: 1850.00. Dif: 0.00. Total ventas: 2200.00"
```

El módulo `diferencias.py` usa regex para extraer el valor de "Dif:".

### Formato en Ticket

```
--- DIFERENCIA MES ---
Acumulado: +$150.00
--------------------------------

--- DIFERENCIA HISTORICA ---
Acumulado: -$250.00
--------------------------------
```

Positivo = sobrante acumulado
Negativo = faltante acumulado

## Multi-Caja (Franquicias)

En modo cadena/franquicia con múltiples cajas:

1. **Vista consolidado**: Muestra métricas de todas las cajas
   - Solo lectura (no permite arqueo)
   - Tabla con estado de cada caja

2. **Corte por caja**: Debe seleccionarse una caja específica
   - Usar combo o doble clic en tabla
   - Arqueo individual por terminal

3. **Resumen tienda**: `MotorCierre.resumen_tienda()`
   - Consolidado de todas las cajas
   - Agrupado por caja_id

## Integración con UI

### Cajero (paso5)
```python
from src.ui_global.cierre_diario_ui.cierre_main_ui import CierreGlobalUI

ui = CierreGlobalUI(parent_main=main_window, is_terminal=True, force_z=False)
# is_terminal=True → modo cajero
# force_z=False → modo turno (cierra X)
```

### Admin/Jefe
```python
from src.admin.cierre.cierre_main import Admin7Cierre

ui = Admin7Cierre(parent_main=main_window)
# Hereda de CierrePremiumUI
# Permite modo día (cierre Z) y consolidado multi-caja
```

## Configuración

En `config.json`:
```json
{
  "caja_id": 1,
  "ticket_printer": "EPSON_TM-T20II",
  "ticket_printer_2": "Star_SP700"
}
```

## Base de Datos

### Tablas relacionadas

**ventas**:
- `estado`: 'COMPLETADA', 'CERRADA'
- `metodo_pago`: Método de pago usado
- `pago_efectivo`: Monto en efectivo
- `cambio`: Vuelto entregado
- `cliente_nombre`: Nombre del cliente (opcional)
- `caja_id`: ID de la caja
- `usuario`: Cajero que realizó la venta

**movimientos_caja**:
- `tipo`: 'APERTURA', 'CIERRE_TURNO', 'CIERRE_Z', 'INGRESO', 'RETIRO'
- `monto`: Monto del movimiento
- `observaciones`: Detalles (incluye diferencia)
- `caja_id`: ID de la caja
- `usuario`: Operador
- `fecha`: Timestamp

## Compatibilidad

- **SQLite**: Base de datos local por defecto
- **MariaDB**: Base de datos en red (modo cadena)
- **Windows**: Soporte completo
- **Linux**: Parcial (sin win32print)

## Testing

Para probar el módulo:

```python
# Prueba de cálculo de totales
from src.cerebro_global.cierre_caja_cerebro import MotorCierre

datos = MotorCierre.obtener_datos_cierre_diario()
print(f"Total ventas: {datos['v_totales']}")
print(f"Efectivo esperado: {datos['v_caja_total']}")

# Prueba de diferencias
from src.cerebro_global.cierre_caja_cerebro.procesos.diferencias import (
    calcular_diferencia_mes,
    calcular_diferencia_historica
)

dif_mes = calcular_diferencia_mes(caja_id=1)
dif_hist = calcular_diferencia_historica(caja_id=1)
print(f"Diferencia mes: {dif_mes}")
print(f"Diferencia histórica: {dif_hist}")
```

## Mantenimiento

### Reglas de negocio

1. **Solo se puede cerrar una caja abierta**
   - Verifica último movimiento no sea CIERRE_TURNO/CIERRE_Z

2. **Fechas pasadas son solo lectura**
   - No permite cerrar días anteriores
   - Permite consultar historial

3. **En modo cadena, el corte es por caja**
   - No existe cierre global de todas las cajas
   - Debe seleccionarse caja específica

4. **Ventas pasan a CERRADA al cerrar**
   - Evita doble conteo en cierres sucesivos
   - Permite rastreo de estado

### Errores comunes

**"La caja ya se encuentra cerrada"**:
- Ya existe un movimiento de cierre después de la última apertura
- Solución: Realizar apertura de caja primero

**"Debe elegir una caja concreta"**:
- Intentando cierre Z en modo consolidado
- Solución: Seleccionar caja específica en combo

**Diferencia de cálculo**:
- El esperado incluye abonos e ingresos
- Verificar que se contó todo el efectivo físico

## Roadmap

Próximas mejoras planeadas:
- [ ] Exportación a PDF/Excel de reportes
- [ ] Gráficos de tendencias de diferencias
- [ ] Alertas automáticas por diferencias fuera de rango
- [ ] Integración con sistemas contables externos
- [ ] Firma digital en tickets de cierre
