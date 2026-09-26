# Paneles

## Qué hace

El cuerpo del catálogo: filtros + grilla + pie. No es la venta; solo administración de productos.

## Funciones

| Archivo | Clase | Rol |
|---------|--------|-----|
| `catalogo_productos.py` | `CatalogoProductos` | Junta filtros, tabla y pie; carga, alta, Excel, precarga |
| `catalogo_productos.py` | `MotorBusquedaInventario` | Hilo: `InventarioService.obtener_lista_de_productos` |
| `tabla_inventario.py` | `TablaInventario` | Grilla: oferta (lectura) + mayoreo (2 cols); Stock al final |

## Cómo corre

1. Filtro cambia → hilo de búsqueda → `popular` en la tabla.
2. Scroll cerca del final → siguiente página de 50.
3. Doble clic / botón → `DialogoProducto` → `InventarioService.guardar_producto`.

Columnas oferta: `Cant. of.`, `P. oferta`, `Relámpago` (solo lectura en grilla; se cargan en Ofertas). Mayoreo: `Cant. may.` / `P. mayoreo` (también desde jefe Promedios vía `MotorMayoreo`).

## Si falla

Lista vacía o mensaje del service; no abre venta.

## Qué no debe cambiar

No editar oferta desde el diálogo de inventario como dueño de cartelería. No imprimir carteles desde este panel.
