# Empujar inventario a maestra

Qué hace: si esta caja no tiene MariaDB, manda el producto a la PC maestra.

Qué función: `empujar_producto_a_maestra`.

Cómo funciona: POST JSON a `:8000/api/productos/upsert` con `pedir_a_maestra`. Si MariaDB ya está, no duplica el producto: avisa a la TV (`aviso_tv`). Si el host es esta misma PC, no envía el upsert.

Qué no debe cambiar: no reemplazar MariaDB cuando ya está conectada.
