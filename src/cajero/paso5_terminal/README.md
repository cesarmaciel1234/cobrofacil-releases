# Paso 5 — terminal

La venta. El archivo `paso5_terminal.py` junta la pantalla. Termina en la línea 2427. La clase `Paso5Terminal` tiene 81 métodos.

`parse_float_safe` está en este archivo, una sola vez, fuera de la clase. Lee un texto con `$`, punto de miles y coma decimal. Si no puede, devuelve `0.0`.

`Paso5Terminal._precalentar_cobro` importa `Paso6Cobro` adentro del método. Lo dispara `QTimer.singleShot(1200, ...)`. En el ejecutable ese import es el que espera, y la venta ya está pintada.

La punta de esta rama es `punta del piramide.md`. Cada carpeta de adentro tiene su README.

No partir este archivo en `event_handlers.py`, `state_manager.py` ni `validators.py`. No mover el import de `Paso6Cobro` al tope.

Lo que parece duplicado y se queda está en `src/cajero/README.md`, sección «Parece un defecto y no se toca»: los dos `hideEvent`, el `except` del multiplicador, el de los combos, el `import winsound` del hilo y el `if __name__ == "__main__":`.
