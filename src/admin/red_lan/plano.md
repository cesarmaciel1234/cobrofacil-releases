# Plano — servidor LAN admin

La rama arranca acá. El wrapper que abre el admin está en `src/admin/legacy/admin6_red_lan.py` (índice 6). Esta carpeta es la pantalla actual. La conversión a MAESTRA se ofrece para reparar una config esclava solo cuando el host configurado es una IP de esta misma PC y MariaDB local responde; al confirmar, la conexión se normaliza y el oficio se reinicia.

## Frente

Maestra / esclava. Si `db_host` es una IP propia y MariaDB local responde, permite reparar el perfil a MAESTRA con confirmación; el dashboard no importa el sync: solo emite el índice 6.

## Fondo

Configura el nodo y, al reparar el rol, normaliza la conexión a `localhost` y reinicia el oficio del servidor. El catálogo y las ventas viajan por `base_de_datos` / sync. Esta pantalla no reescribe stock ni costo. Si la maestra no contesta, el TPV queda en modo offline.

## Ecosistema

Pide y envía réplica. No calcula fórmulas ni promociones.
