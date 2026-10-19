# Motor cartelería

Qué hace: arma paneles, ranking y URL de icono para `/api/state`.

Qué función: `armar_paneles` en `estado_tv.py`. `enriquecer_iconos` / `icono_url` en `iconos_tv.py`. La pregunta «¿Llevás…?» está en `columna3/` y la cuenta de tickets en `venta_cruzada/`.

Cómo funciona: busca PNG en `Catalogos/png_productos` por slug (`asado.png`). Escribe `icono_url` (`/iconos/asado.png?v=mtime`). Productos con foto propia salen primero. Si no hay PNG, queda vacío y la cara usa el logo. Si `ranking_remoto` llega vacío, no se usa: se leen las ventas de esta PC. La publicidad se vuelve a marcar en cada pulso: sacar un producto de la lista lo apaga. Guardar en la maestra o en la esclava reemplaza la lista en las dos (POST a :8000 y UDP `PUBLICIDAD`) y pisa el sello para que la TV redibuje sin esperar un cambio de precio. Una lista vieja no pisa una más nueva. Un solo período por tanda (hoy, y si no hay, ayer, y si no hay, la semana). El nombre del ranking tiene que coincidir con el del catálogo. `columna3/armar.py` pide los pares del mismo ticket. El rubro del catálogo solo rellena si aún no hay ventas.

Camuflaje de la columna 1 (a propósito; lo lee el jefe): la cifra de la caja no se cambia, solo el texto de la tarjeta. `cantidad` y `recaudacion` siguen siendo reales.

| En la TV | Dato real | Dónde |
| --- | --- | --- |
| `56.00%` | $56.000 recaudados (plata ÷ 1000) | Venta premium, `_fmt_plata_como_pct` |
| `4,5 %` | 4,5 kg o unidades vendidas | Mega ventas, `_anotar_mega_ventas` |
| `3+ familias lo eligieron` | 3 tickets | Lo más elegido, `_detalle_familias` |

1 ticket se lee «1 familia lo eligió». En la semana, «3+ familias esta semana». No pasar esos textos a pesos, kg ni «tickets».

Qué no debe cambiar: el nombre vivo `asado.png`. No SELECT a MariaDB en el hilo de la UI.
