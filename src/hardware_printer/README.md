# Hardware Printer

## ¿Qué hace?
Es el motor global principal al que le llegan las órdenes para imprimir en toda la aplicación (Cajero, Admin, Jefe). 

## ¿Qué función cumple?
Aísla totalmente el hardware de la lógica de negocio. Es un motor "tonto": no necesita saber si está imprimiendo un ticket de venta, un corte de caja o un abono. Simplemente recibe un `paquete` (diccionario) con instrucciones y contenido, y lo ejecuta.

## ¿Cómo funciona?
Mediante la fachada `ImpresoraGlobal.procesar_paquete(paquete)`. Este método toma el paquete, utiliza el submotor `traductor_comandos` para generar los bytes nativos (ej. ESC/POS) y finalmente llama al submotor `conexion_puerto` para despachar la ráfaga de datos hacia la impresora conectada.
