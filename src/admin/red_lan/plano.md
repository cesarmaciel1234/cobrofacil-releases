# Plano — servidor LAN admin

La rama arranca acá. El wrapper que abre el admin está en `src/admin/legacy/admin6_red_lan.py` (índice 6). Esta carpeta es la pantalla actual.

## Frente

Maestra / esclava. El dashboard no importa el sync: solo emite el índice 6.

## Fondo

Configura el nodo. El catálogo y las ventas viajan por `base_de_datos` / sync. Esta pantalla no reescribe stock ni costo. Si la maestra no contesta, el TPV queda en modo offline.

## Ecosistema

Pide y envía réplica. No calcula fórmulas ni promociones.
