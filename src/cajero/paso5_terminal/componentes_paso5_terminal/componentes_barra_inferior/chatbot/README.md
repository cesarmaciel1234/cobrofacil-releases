# Módulo: Chatbot Autónomo (Asistente del Cajero)

**Estado Arquitectónico:** Blindado y Autónomo (Process Isolation).

## ¿Qué hace y cómo funciona?
Este es el asistente de ayuda para el cajero. A diferencia de otros widgets de la interfaz, este chatbot **NO se ejecuta dentro del hilo principal de PyQt (TPV)**. 
Para evitar que un error, pérdida de memoria o cuelgue del asistente congele la caja en pleno cobro, se estructuró como un ejecutable completamente independiente.

### Reglas de Comportamiento y Posición (¡IA, NO ROMPER ESTO!)
1. **Lanzador Desacoplado:** El botón de la barra inferior del Cajero (main_window.py -> _toggle_chatbot_overlay) lanza chat_bot.py usando subprocess.Popen. Es un proceso OS distinto.
2. **Transferencia de HWND:** Al lanzarlo, el TPV le pasa su winId() (DNI de la ventana) como argumento (sys.argv[1]) para que el bot conozca al TPV.
3. **Posición Inicial:** Al arrancar, el bot ejecuta ctualizar_posicion(), anclándose automáticamente en la esquina inferior derecha de la pantalla para no tapar los tickets.
4. **Draggable (Movible):** Tiene WindowStaysOnTopHint y FramelessWindowHint. Los eventos mousePressEvent y mouseMoveEvent están sobreescritos para que el usuario pueda arrastrarlo desde cualquier lugar.
5. **Auto-Foco del Cursor:** Usa un QTimer.singleShot(150) en el showEvent para clavar el cursor en la caja de texto apenas aparece. Cero clics extra.
6. **El Guardián de Foco (2 Segundos):** Si el bot tiene el foco de Windows y el usuario **deja de escribir durante 2 segundos**, el bot asume inactividad. Inmediatamente invoca a la API de Windows (ctypes.windll.user32.SetForegroundWindow(hwnd)) para **forzar la devolución del foco de pantalla al TPV**. Esto blinda el escáner (evita que un código de barras vaya a parar al chat).
7. **Auto-Kill al Escanear:** En main_window.py, la señal 	xt_scan.textChanged está conectada a _auto_cerrar_chatbot. Si el cajero escanea un producto o teclea algo en el buscador principal del TPV mientras el bot está abierto, el TPV **mata el proceso del chatbot instantáneamente**, limpiando la pantalla y restaurando la agilidad visual de la venta.

## Archivos Clave
- chat_bot.py: Código fuente autónomo de la ventana del chatbot (GUI, timers y FindWindowW).
- manual_cajero.json: Diccionario estático donde el bot busca coincidencias (
egex/normalización) para responder preguntas.
