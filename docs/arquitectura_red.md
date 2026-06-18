# Arquitectura del Motor de Red (Network Engine)

Este documento describe la arquitectura interna de las comunicaciones entre las diferentes terminales (Cajero, Jefe, Administrador) de CobroFacil POS.

## 1. El Motor de Red (`network_engine.py`)

El Motor de Red es el "Cerebro de Comunicaciones" del sistema. Su objetivo principal es mantener a todas las computadoras informadas de quién está conectado y activo sin interferir con las tareas de cobro o la base de datos.

Está modularizado en tres componentes clave:

### A. El Centinela de Latidos (Heartbeat Worker)
Es un hilo de ejecución en segundo plano (`threading.Thread` en modo daemon/agente). Su única responsabilidad es ejecutar un ciclo infinito que, cada 3 segundos, emite una señal para indicar que la computadora está activa.
- **Ventaja:** Al estar en un hilo separado, no se congela si la interfaz gráfica de usuario (UI) principal se bloquea o si se está realizando una consulta pesada a la base de datos.

### B. El Puente de Señales (`_trigger_heartbeat_signal`)
Dado que PyQt (el framework gráfico) no permite interactuar con los sockets de red desde hilos en segundo plano por razones de seguridad de memoria, se utiliza una `pyqtSignal`. 
- **Funcionamiento:** El Centinela de Latidos emite esta señal, la cual es atrapada por el hilo principal. El hilo principal entonces utiliza `QUdpSocket` para enviar el latido físico a través de la red LAN y a la propia computadora (Loopback) mediante la bandera `ShareAddress | ReuseAddressHint`.

### C. La Antena Receptora (`_read_pending_datagrams`)
Es la función encargada de escuchar constantemente el puerto UDP (38000).
- **Procesamiento:** Cuando recibe un mensaje de tipo `HEARTBEAT` de otra terminal, actualiza un registro interno de "última vez visto".
- **Timeout:** Si el Panel de Administración no recibe un latido de una caja específica durante 10 segundos, asume que la caja se desconectó, apagando la luz verde y registrando la alerta en la bitácora.

## 2. El Chatbot Espía (Che Lobo)

El Chatbot interactivo funciona como un microservicio independiente. Escucha en el puerto UDP 45680.
Para permitir simulaciones locales (varios perfiles abiertos en la misma PC), el Chatbot utiliza `QUdpSocket.ShareAddress | QUdpSocket.ReuseAddressHint`, lo que permite que múltiples instancias convivan sin bloquear el puerto.

- **Detección de Tickets:** Cuando el Cajero agrega un producto a la tabla de ventas, la terminal emite un datagrama UDP `TICKET_UPDATE|Total`.
- **Reacción:** El Chatbot intercepta este mensaje, inyecta un código JavaScript en su motor web (`recibirRespuesta`) y se hace visible automáticamente en la pantalla del usuario con la información actualizada de la venta.
