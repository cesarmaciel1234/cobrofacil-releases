# Submódulo: Conexión de Puerto

## ¿Qué hace?
Se encarga exclusivamente de abrir el canal de comunicación físico (USB, Serial, Ethernet) con la impresora de tickets y mandar los bytes.

## ¿Qué función cumple?
Es la última milla del sistema. Aísla librerías como `pyserial`, `win32print` o `sockets` del resto de la aplicación. Además, provee tolerancia a fallos en caso de impresora desconectada (Modo Offline).

## ¿Cómo funciona?
`enviador_datos.py` define `enviar(datos: bytes)`. Intenta abrir el puerto, escribir el buffer y cerrar la conexión de forma segura. Retorna `True` si la operación se concretó. Respeta la regla de simulación en CI para no bloquear la ejecución.
