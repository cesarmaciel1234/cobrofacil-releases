# Vistas

## Qué hace

Pantalla raíz del módulo Inventario: menú de pestañas y vuelta al dashboard admin.

## Función

`Admin1Inventario` en `inventario_main.py`.

## Cómo corre

1. `main_window` / registry instancia `Admin1Inventario`.
2. `_setup_ui` arma el stack: catálogo (`CatalogoProductos`), departamentos, categorías.
3. Guardar / borrar producto llama `InventarioService.guardar_producto` / `borrar_producto`.
4. `request_dashboard` vuelve al panel admin.

## Si falla

Mensaje `QMessageBox`; el service devuelve `(ok, msg)`.

## Qué no debe cambiar

No mezclar con Ofertas/Imprenta. Mantener tema claro. No tocar el cajero.
