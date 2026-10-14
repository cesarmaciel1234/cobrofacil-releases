# Utils

Piezas transversales (DPI, Qt, paths). No es un módulo de pantalla.

## `qt_dpi.py` — escala global (NO TOCAR para un sector)

`configure_process_dpi` fija `QT_SCALE_FACTOR` al arrancar. Eso escala **toda** la app: terminal de caja, admin, jefe, diálogos.

| Hacer | No hacer |
|---|---|
| Agrandar letras/tiles en el módulo (ej. `ConfigButton`) | Subir el piso de `layout_scale` / `max(0.70, …)` por un pantallazo chico |
| Usar `scale_px` solo como ayuda de medida local | “Arreglar baja resolución” cambiando la fórmula global |
| Pedir explícito del usuario si hay que retocar DPI | Mezclar un fix de Configuración / Ofertas / etc. con `qt_dpi` |

Motivo: en laptop 14" un bump de 0.70 → 0.88 agranda cajero y todo lo demás. Modularizar exige que el trabajo en un sector no mueva el zoom del proceso.

Referencia de tipografía local legible: `src/admin/configuracion/componentes/config_button.py` (`max(15, scale_px(16))` en el texto del tile).

## `letra.py` — letras de góndola

Misma lectura que Admin → Etiquetas de góndola.

| Pieza | Función |
|---|---|
| Id / PLU | `fuente_id` / `vestir_id` (Consolas Bold) |
| Nombre | `fuente_nombre` / `vestir_nombre` (Segoe UI Bold) |
| Precio, stock, totales | `fuente_numero` / `vestir_numero` |
| Título de pantalla | `QSS_TITULO` en QLabel |
| Número grande de KPI | `QSS_KPI` en QLabel |

Al tocar un módulo (inventario, promociones, reportes jefe, resto admin/jefe), vestir las tablas con estas funciones. No QSS 900 + `setBold` juntos. No en el cajero. Calendarios: `src/jefe/reportes/letra.py`.
