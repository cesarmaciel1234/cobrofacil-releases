# Plano — navegación de pantallas

La rama arranca acá. El stacked vive en `src/main_window.py`. Esta carpeta solo nombra índices y fábricas.

## Frente

El admin no navega por esta carpeta. Ve tiles en el dashboard. Cada tile emite un índice. `MainWindow.switch_tab` abre esa pantalla.

## Fondo

- `screen_indices.py` (`Screen`): números fijos 0–27. `FREE` son huecos reales (12 y 16). El 15 es configuración de cartelería, no un hueco.
- `screen_registry.py`: las mismas fábricas que `MainWindow._screen_factories`. Si se agrega una pantalla, se actualizan los dos.

Cada módulo es un ecosistema: el hub no importa su motor. Solo pide el índice. El módulo pide y envía datos a su cerebro / servicio. No reescribe el catálogo de otro.

## Qué no cambiar

- No reordenar índices para “ordenar el menú”.
- No marcar como libre un slot que ya tiene fábrica.
- No abrir el cajero (1) ni la TV (21) desde un tile de admin.
