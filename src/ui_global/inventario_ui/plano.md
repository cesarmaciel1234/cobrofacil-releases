# Inventario (admin)

## Frente

Pantalla admin de catálogo: productos, precios, stock, departamentos y categorías. Entrada desde el panel admin (índice inventario / `Admin1Inventario`). Tema claro (`#F8FAFC`).

Pinta: listado con filtros, alta/edición de producto (precio, costo, stock, mayoreo), columnas de oferta en lectura (cant/precio/relámpago), deptos/categorías, Excel, urgencia.

No pinta: edición de promo (Ofertas). Impresión de carteles (Imprenta). Terminal cajero.
## Fondo

1. `vistas/inventario_main.py` → `Admin1Inventario`: pestañas (catálogo, deptos, categorías) y permisos.
2. `paneles/catalogo_productos.py` → `CatalogoProductos`: arma filtros + tabla + pie; busca con `MotorBusquedaInventario`.
3. Datos: `src.services.inventario_service.InventarioService` (`obtener_lista_de_productos`, `guardar_producto`, `borrar_producto`, Excel, nube).
4. Tabla SQLite: `productos` (y tablas de departamentos/categorías vía el service).

No romper: mayoreo se edita acá o desde Promedios jefe (`MotorMayoreo`). Oferta se edita en Ofertas; Inventario solo la muestra. No aplicar `styles.qss` oscuro del cajero.