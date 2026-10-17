# Motor cartelería

Qué hace: arma paneles, ranking y URL de icono para `/api/state`.

Qué función: `armar_paneles` en `estado_tv.py`. `enriquecer_iconos` / `icono_url` en `iconos_tv.py`.

Cómo funciona: busca PNG en `Catalogos/png_productos` por slug (`asado.png`). Escribe `icono_url` (`/iconos/asado.png?v=mtime`). Productos con foto propia salen primero. Si no hay PNG, queda vacío y la cara usa el logo. Si `ranking_remoto` llega vacío, no se usa: se leen las ventas de esta PC.

Qué no debe cambiar: el nombre vivo `asado.png`. No SELECT a MariaDB en el hilo de la UI.
