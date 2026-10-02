# Plano - Servicios del Servidor de Tienda

## Frente
El usuario no interactúa visualmente de forma directa con la mayoría de estos archivos, ya que son procesos que operan de fondo como servicios o demonios (conexión a la base, cola de email, impresiones, cartelería, MercadoPago, onedrive, etc.). 

## Fondo

mariadb_controller.py: Administra el ciclo de vida del proceso de MariaDB (mysqld.exe).
- Asegura reglas de firewall (_ensure_firewall).
- start_server(): Lanza MariaDB. Si el motor falla en arrancar por puertos ocupados o corrupción, realiza chequeos en el .err de la carpeta data. Si detecta un tablespace dañado, elimina los archivos e intenta un start_server() limpio para auto-repararse.
- **Importante (Evitar bucles infinitos):** Si la base está irremediablemente corrupta al extraer un backup, la rutina de auto-reparación tiene un límite de reintentos (_repair_attempt) interno. Tras 3 intentos fallidos, reporta error y aborta en lugar de quedarse en un ciclo infinito de borrado-reinicio.
