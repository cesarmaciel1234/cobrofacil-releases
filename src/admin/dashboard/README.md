# Dashboard admin

Qué hace: Hub del perfil admin. Saludo, fecha y tiles de módulos.

Qué función: `Admin0Dashboard` en `dashboard_main.py`. Cada tile es `AdminCard` (`src/admin/admin_card.py`).

Cómo funciona: las tiles miden 190×160. Clic abre el módulo en este monitor. El **+** (Ctrl+clic o clic derecho) lo manda a otra ventana en el mismo proceso. El orden sigue `module_stats.json`.

Qué no debe cambiar: no precargar inventario, cierre ni Mercado Pago al abrir. No unificar colores con el cajero. No importar motores de los módulos: solo el índice. Plano en `plano.md`.
