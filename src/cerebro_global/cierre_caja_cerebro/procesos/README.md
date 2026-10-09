# Procesos del Cierre de Caja

Este directorio contiene los módulos que implementan la lógica del cierre de caja (Reporte Z/X).

## Estructura Modular

### `totales.py`
**Responsabilidad**: Cálculo de totales de ventas y movimientos para el panel de cierre.

Funciones principales:
- `obtener_datos_cierre(fecha_str, cajero, caja_id, db)`: Devuelve todos los totales del período
- `_ultima_apertura(db, caja_id, cajero)`: Obtiene fecha y monto de la última apertura de caja
- `_empty()`: Diccionario vacío con estructura de datos por defecto

Datos devueltos:
- Ventas por método de pago (efectivo, tarjeta, transferencia, etc.)
- Fondo de apertura
- Abonos de clientes desglosados por método
- Movimientos manuales (ingresos/egresos)
- Diferencias acumuladas (mes e histórica)

### `diferencias.py`
**Responsabilidad**: Cálculo de diferencias acumuladas de caja.

Funciones principales:
- `calcular_diferencia_mes(caja_id, db)`: Diferencia acumulada desde el 1° del mes actual
- `calcular_diferencia_historica(caja_id, db)`: Diferencia acumulada total desde el inicio
- `_extraer_diferencia_de_observacion(observacion)`: Extrae el valor numérico de una observación de cierre

Lógica:
- Busca movimientos de tipo 'CIERRE_TURNO' o 'CIERRE_Z'
- Extrae el valor de "Dif:" de las observaciones usando regex
- Suma todas las diferencias (positivo = sobrante, negativo = faltante)

### `cierre.py`
**Responsabilidad**: Ejecución del cierre de caja y registro en base de datos.

Funciones principales:
- `cerrar_caja(username, caja_id, fisico, dif, esperado, t_total, modo)`: Ejecuta el cierre
- `_apertura_fecha(db, caja_id, username)`: Obtiene fecha de la última apertura
- `_insertar_movimiento(...)`: Registra el movimiento de cierre
- `_celda(row, clave, indice)`: Helper para acceder a celdas de resultados

Lógica:
- Valida que la caja no esté ya cerrada
- Registra movimiento de caja con observaciones
- Actualiza estado de ventas a 'CERRADA'
- Maneja compatibilidad con MariaDB antiguo

### `esperado.py`
**Responsabilidad**: Cálculo del efectivo esperado en caja.

Funciones principales:
- `efectivo_esperado_caja(caja_id, db)`: Usa db_manager.get_efectivo_en_caja
- `movimientos_turno(caja_id, desde_fecha, db)`: Retorna (entradas, salidas) del turno

### `modos.py`
**Responsabilidad**: Normalización de modos de cierre.

Funciones principales:
- `normalizar_modo(modo)`: Convierte variaciones a 'cajero' o 'dia'
- `etiqueta_modo(modo)`: Devuelve etiqueta legible ('Cierre de Turno' o 'Cierre Z')
- `tipo_movimiento_cierre(modo)`: Devuelve tipo de movimiento ('CIERRE_TURNO' o 'CIERRE_Z')

### `historial_cortes.py`
**Responsabilidad**: Consulta de cortes ya realizados.

Funciones principales:
- `listar_cortes_del_dia(fecha_str, caja_id, cajero)`: Lista de cortes del día
- `resumen_cortes_por_cajero(fecha_str, caja_id)`: Resumen agrupado por cajero

### `multi_caja.py`
**Responsabilidad**: Gestión de múltiples cajas (modo cadena/franquicia).

Funciones principales:
- `listar_caja_ids()`: Lista de IDs de cajas configuradas
- `resumen_multi_caja(fecha_str)`: Resumen consolidado de todas las cajas

## Flujo de Datos

```
UI (cierre_main_ui.py)
    ↓
MotorCierre.obtener_datos_cierre_diario()
    ↓
totales.obtener_datos_cierre()
    ├─ esperado.efectivo_esperado_caja()
    ├─ esperado.movimientos_turno()
    ├─ diferencias.calcular_diferencia_mes()
    └─ diferencias.calcular_diferencia_historica()
    ↓
UI muestra métricas y arqueo
    ↓
Usuario cierra caja
    ↓
MotorCierre.cerrar_caja()
    ↓
cierre.cerrar_caja()
    ├─ Valida estado
    ├─ Inserta movimiento
    └─ Actualiza ventas a CERRADA
    ↓
UI imprime ticket
    ↓
printer.imprimir_ticket_z()
    ↓
ticket_z.formatear_ticket_z()
    ↓
Envío a impresora ESC/POS
```

## Dependencias

Módulos internos:
- `src.base_de_datos.database.db_manager`: Gestión de base de datos
- `src.config.config`: Configuración del sistema

Librerías externas:
- `datetime`: Manejo de fechas
- `re`: Expresiones regulares (para extraer diferencias)
- `typing`: Type hints

## Compatibilidad

- **SQLite**: Base de datos local por defecto
- **MariaDB**: Base de datos en red (modo cadena/franquicia)
- **Windows**: Impresión vía Spooler (win32print)
- **Serial**: Impresión directa a puerto COM (pyserial)
