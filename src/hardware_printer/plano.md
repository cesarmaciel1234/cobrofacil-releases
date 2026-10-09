# Plano del Hardware Printer

Esta carpeta implementa el motor de impresión como un ente "tonto" siguiendo el modelo de "encarpetado piramidal documentado".

- `motor_impresion.py`: Fachada principal. Define `ImpresoraGlobal`. Recibe un paquete genérico y lo manda a traducir y enviar.
- `traductor_comandos/`: Submódulo responsable de convertir el paquete genérico en bytes (ESC/POS u otros lenguajes de impresión).
- `conexion_puerto/`: Submódulo responsable de la conexión física (USB, RED, COM) y el envío crudo.
