# Servidor de Tienda

## Qué hace

`src/central_red_global/lan_server.py` publica la API HTTP para las cajas y el descubrimiento UDP para encontrar la maestra. Esta carpeta organiza el arranque, el rol (maestra/esclava), la presencia y la ventana del proceso `--server`.

## Funciones principales

- `init_lan_server()`: inicia una sola supervisión para HTTP y UDP.
- `start_http_server()`: atiende peticiones API en paralelo, con un máximo de 32 solicitudes activas. Al fallar el enlace o el servicio, informa y reintenta cada cinco segundos.
- `start_udp_discovery_server()`: responde a descubrimientos de la tienda y vuelve a enlazar el puerto si el servicio se interrumpe.
- `stop_lan_server()`: solicita un apagado ordenado.
- `servidor/oficio/`: decide qué tareas corresponden a la maestra o a la esclava.
- `servidor/arranque/`: inicia servicios y proceso; `servidor/ventana/` solo los muestra y permite controlarlos.

## Cómo funciona

La maestra expone su API en TCP 8000 y escucha descubrimientos en UDP 37020. Las solicitudes HTTP se sirven con hilos limitados para que una conexión lenta no bloquee a todas las cajas y para no crear un número ilimitado de hilos. Si no puede abrir un puerto o el bucle del servidor se detiene, el supervisor conserva el proceso y reintenta. La esclava no debe iniciar estos servicios como si fuera titular.

El límite de concurrencia no reemplaza MariaDB ni una prueba de carga. Antes de una actualización de producción, probar con varias cajas y con MariaDB real.

## Qué no debe cambiarse

- No anunciar como maestra un puesto esclavo ni una base SQLite.
- No borrar colas offline al detener o reiniciar el servidor.
- No convertir un error de servicio en una respuesta exitosa.
- Mantener acotada la concurrencia del servidor HTTP.
