# Átomos

## Qué hace

Piezas chicas sin lógica de negocio: el pie del catálogo.

## Función

`PieInventario` en `pie_inventario.py`.

## Cómo corre

`CatalogoProductos` llama `actualizar_totales(total, sin_stock)` y opcionalmente texto de selección. Muestra cantidad de productos y alerta de stock crítico (colores del `theme_manager`).

## Si falla

No falla solo: si no lo llaman, queda en «0 productos».

## Qué no debe cambiar

Solo lectura informativa; no edita stock ni abre diálogos.
