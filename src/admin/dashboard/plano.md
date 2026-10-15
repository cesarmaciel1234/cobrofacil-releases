# Plano — dashboard admin

La rama arranca acá. Es la pantalla 0 del perfil admin.

```
admin/dashboard/
  plano.md
  dashboard_main.py     Admin0Dashboard
  module_stats.json     orden de tiles por uso
```

## Frente

Tras el login de admin se ve el hub: saludo, fecha y tiles (inventario, ofertas, cierre, MP, clientes, etc.). No hay telón de partículas. Cada tile abre su módulo la primera vez que se toca.

## Fondo

`main.py` con `--role admin` arma `MainWindow` y `apply_roles` instancia solo esta pantalla. `switch_tab(0)` no pega a la maestra. Inventario, cierre y Mercado Pago no se precargan: en el ejecutable esa precarga congelaba el hub. El dashboard no importa `db_manager`.

## Qué no cambiar

- No precargar inventario (2), cierre (7) ni MP (10) al abrir admin.
- No mostrar `WelcomeOverlay` en este perfil.
- No unificar colores con el cajero.
