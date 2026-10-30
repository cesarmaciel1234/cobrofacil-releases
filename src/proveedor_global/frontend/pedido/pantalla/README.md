# Pantalla

## Qué hace la carpeta
La pantalla de faltantes: tarjetas, filtro, tabla y mensaje de WhatsApp.

## Qué función, con el nombre real
* `PanelPedidosAutomaticos`: arma la pantalla y arranca el hilo.
* `PanelPedidosAutomaticos._pintar_resumen`: pinta lo que el hilo ya trajo.
* `PanelPedidosAutomaticos._pintar_kpis`: las tres tarjetas siguen el proveedor elegido.
* `PanelPedidosAutomaticos._copiar_whatsapp`: copia el texto.

## Cómo funciona, en el orden en que corre
1. `refrescar_datos` arranca `HiloReposicion`. Pedidos autónomos muestra lo suelto. Pedido bulto muestra la fórmula y el stock de adentro. El mensaje sigue al botón que está activo.
2. Todos arma un solo mensaje, sin ficha. Un proveedor arma solo el suyo.
3. Cambiar la cantidad rearma el mensaje y las tarjetas. No escribe el stock. Lo que está dentro de una fórmula se ve en gris, con su stock, y no entra al mensaje. El pedido de pollo (caja, o en el caso extremo los kilos de suprema o de pata) sale de `src/proveedor_global/frontend/formula/motores/caja_pollo.py`.
4. Guardar mínimo y máximo sale por `HiloGuardarPiso`.
5. Al pintar, `sugerir.preparar` anota el stock del suelto y, si el proveedor ya tiene días, calcula la cantidad. Un stock en cero dice que nos quedamos cortos. Sin movimiento, no pide de más. La compra vieja no se repite.

## Qué devuelve cuando falla
Si el hilo no trae pedidos, la pantalla queda en cero.

## Qué no debe cambiar una mejora futura
No escribir `productos` desde acá, salvo el piso y el techo por su hilo.
