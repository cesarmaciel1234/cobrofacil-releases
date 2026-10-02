# Plano - Red Global (LAN y Sync)

## Frente
El sistema coordina la presencia de la tienda en red. La PC Maestra actúa como servidor. Los clientes LAN (Cajas esclavas, impresoras de red) detectan al servidor de manera automática por UDP (puerto 37020) y luego consumen su API REST (puerto 8000) o MariaDB (3306).

## Fondo

etwork_engine.py: Lanza los servicios de red según el perfil (maestra o esclava).
lan_server.py: API LAN (FastAPI).
master_presence.py: Determina si la máquina actual debe comportarse como el hub principal.
