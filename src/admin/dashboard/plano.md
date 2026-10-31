# Plano — dashboard admin

La rama arranca acá. Es la pantalla 0 del perfil admin.

```
admin/dashboard/
  plano.md
  dashboard_main.py     Admin0Dashboard
  module_stats.json     orden de tiles por uso
```

## Frente

Tras el login de admin se ve el hub: saludo, fecha y tiles (inventario, ofertas, cierre, MP, clientes, etc.). Cada tile mide **190×160**. El **+** (también Ctrl+clic o clic derecho) manda el módulo a otra ventana **en el mismo proceso** (`ventanas_sueltas/`, tope 3). Clic normal abre en este monitor. No hay telón de partículas. El lanzador, si Admin ya corre, enfoca esa ventana: no abre otro `.exe`.

## Fondo

`main.py` con `--role admin` arma `MainWindow` y `apply_roles` instancia solo esta pantalla. `switch_tab(0)` no pega a la maestra. Inventario, cierre y Mercado Pago no se precargan: en el ejecutable esa precarga congelaba el hub. El dashboard no importa `db_manager`.

Cada tile es un ecosistema: clic → `request_screen(Screen.*)`. Auditoría es `Screen.AUDITORIA` (25). El hub no carga el motor del módulo.

## Qué no cambiar

- No precargar inventario (2), cierre (7) ni MP (10) al abrir admin.
- No mostrar `WelcomeOverlay` en este perfil.
- No unificar colores con el cajero.
- No abrir un segundo `--role admin` para “otro monitor”.
