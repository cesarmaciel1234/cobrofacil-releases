# Plano — hardware admin

La rama arranca acá. Diagnóstico de impresora, cajón y balanza del perfil admin (índice 13).

## Frente

`hardware_main.py`, clase `Admin13Hardware`. Tile «Hardware y Test» del dashboard. Tema claro. Prueba puertos y drivers. No es el cobro.

## Fondo

Lee `config` y hardware local. No escribe `productos`. Si el cajón o la impresora no contestan, informa; el resto del admin sigue. En CI sin hardware eso es modo offline, no un fallo de release.

## Ecosistema

Pide estado al dispositivo. Envía un comando de prueba. No importa el motor de inventario ni el de ventas.
