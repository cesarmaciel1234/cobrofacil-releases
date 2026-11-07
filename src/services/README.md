# Servicios de la aplicación

Esta carpeta contiene servicios de fondo que conectan la aplicación con MariaDB, la red y otros procesos.

`db_network_service.py` contiene un punto de entrada de compatibilidad para el descubrimiento de la maestra. Usa `pareja/buscar.py` para validar la identidad estable `store_id`; no cambia a otra tienda. El ciclo activo inicia la verificación desde `base_de_datos/core/connection.py`; la reconexión de una sesión abierta se coordina en `base_de_datos/repos/red.py` y conserva la cola offline.

`plano.md` describe el arranque del Servidor de Tienda y sus servicios.
