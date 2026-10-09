# Submódulo: Traductor de Comandos

## ¿Qué hace?
Convierte un diccionario genérico en una ráfaga de bytes compatibles con la impresora.

## ¿Qué función cumple?
Desacopla la lógica de estructuración de las secuencias de escape nativas del hardware (ESC/POS, TSPL, etc.).

## ¿Cómo funciona?
El archivo `generador_escpos.py` implementa la función `traducir(paquete)` que itera sobre las líneas y acciones solicitadas, apilando los comandos hexadecimales correspondientes en un `bytearray` que se devuelve listo para su envío.
