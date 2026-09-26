# Moléculas

## Qué hace

Piezas de UI reutilizables del inventario: filtros, diálogos y paneles de deptos/categorías.

## Funciones

| Archivo | Clase | Rol |
|---------|--------|-----|
| `filtros_inventario.py` | `FiltrosInventario` | Buscar, departamento, check Urgencia → señales `filtros_cambiados` / `urgencia_toggled` |
| `dialogo_producto.py` | `DialogoProducto` | Alta/edición de un producto (precio, costo, stock, mayoreo, etc.) |
| `panel_departamentos.py` | `PanelDepartamentos` | ABM departamentos |
| `panel_categorias.py` | `PanelCategorias` | ABM categorías |
| `dialogo_galeria_iconos.py` | `DialogoGaleriaIconos` / `DialogoCargarPng` | Iconos PNG de productos |
| `dialogo_catalogo_clientes.py` | `DialogoCatalogoClientes` / `abrir_catalogo_clientes` | Catálogo para clientes (PDF/imprenta lo puede llamar) |

## Cómo corre

Filtros emiten → catálogo recarga. Diálogo acepta → service guarda. Galería escribe archivos de icono y asocia al producto/depto.

## Si falla

Diálogo cancela o muestra el `msg` del service.

## Qué no debe cambiar

Mayoreo se carga en el diálogo de producto / inventario, no en el hub de promociones. Urgencia solo cambia config de venta sin stock, no borra stock.
