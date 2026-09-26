# Motor de promedios

## Qué hace

Cálculo de merma/costo y puente con inventario vía mayoreo global.

## Funciones

| Función | Rol |
|---------|-----|
| `calcular_media_res` | Merma y costo real $/kg |
| `recalcular_fila` | % ganancia ↔ precio venta |
| `exportar_a_inventario` | Llama `MotorMayoreo.aplicar_desde_promedios` |
| `sincronizar_inventario` | Lee mayoreo/precio con `MotorMayoreo.obtener_por_nombre` |
| `guardar_historial` / `obtener_historial` | Historial SQL |

## Cómo corre

1. Usuario edita cortes en la UI.
2. Exportar → mayoreo + precio lista en `productos`.
3. Sincronizar → trae valores desde inventario a la grilla.

## Si falla

`0` actualizados; historial `False`.

## Qué no debe cambiar

No volver a escribir `precio_oferta_promedio`. Mayoreo se modifica también desde Inventario (mismo motor).
