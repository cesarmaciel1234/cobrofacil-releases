# Plano - Servicios del Servidor de Tienda

## Frente
El usuario no interact�a visualmente de forma directa con la mayor�a de estos archivos, ya que son procesos que operan de fondo como servicios o demonios (conexi�n a la base, cola de email, impresiones, carteler�a, MercadoPago, onedrive, etc.).

## Fondo

`db_network_service.py`: punto de entrada de compatibilidad para descubrimiento de tienda por UDP. La ruta activa de conexión verifica desde `base_de_datos/core/connection.py`; `store_id` impide enlazar otra tienda y la reconexión conserva las colas offline.

mariadb_controller.py: Administra el ciclo de vida del proceso de MariaDB (mysqld.exe).
- Asegura reglas de firewall (_ensure_firewall).
- start_server(): Lanza MariaDB. Si el motor falla en arrancar por puertos ocupados o corrupci�n, realiza chequeos en el .err de la carpeta data. Si detecta un tablespace da�ado, elimina los archivos e intenta un start_server() limpio para auto-repararse.
- **Importante (Evitar bucles infinitos):** Si la base est� irremediablemente corrupta al extraer un backup, la rutina de auto-reparaci�n tiene un l�mite de reintentos (_repair_attempt) interno. Tras 3 intentos fallidos, reporta error y aborta en lugar de quedarse en un ciclo infinito de borrado-reinicio.
