# Moléculas

## Qué hace

Piezas de UI reutilizables del inventario: filtros, diálogos y paneles de deptos/categorías.

## Funciones

| Archivo | Clase | Rol |
|---------|--------|-----|
| `filtros_inventario.py` | `FiltrosInventario` | Buscar, departamento y «No vender sin stock». Sin marcar, el stock sigue en -1, -2, -3 hasta la carga. |
| `dialogo_producto.py` | `DialogoProducto` | Alta/edición. Al abrir un producto carga su código (o el id si el código está vacío), el nombre y los precios. No busca otro producto. En un alta, Enter en el código busca si ya existe. |
| `panel_departamentos.py` | `PanelDepartamentos` | ABM departamentos |
| `panel_categorias.py` | `PanelCategorias` | ABM categorías |
| `dialogo_galeria_iconos.py` | `DialogoGaleriaIconos` / `DialogoCargarPng` | Iconos PNG de productos |
| `dialogo_catalogo_clientes.py` | `DialogoCatalogoClientes` / `abrir_catalogo_clientes` | Catálogo para clientes (PDF/imprenta lo puede llamar) |

## Cómo corre

Filtros emiten → catálogo recarga. Diálogo acepta → service guarda. Al reabrir, la ficha carga el mismo código, nombre, precio y stock. Galería escribe archivos de icono y asocia al producto/depto.

## Si falla

Diálogo cancela o muestra el `msg` del service.

## Qué no debe cambiar

Mayoreo se carga en el diálogo de producto / inventario, no en el hub de promociones. «No vender sin stock» solo cambia si el cajero puede vender sin existencia. No borra stock. Sin marcar, el stock baja a -1, -2, -3 hasta la carga.
