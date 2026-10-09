# Encabezado del Ticket

**Qué hace:** Genera la primera parte del ticket impreso.
**Qué función:** `generar_encabezado` en `generador.py`
**Cómo funciona:** Toma nombre de empresa, dirección, cuit y estado de venta. Inserta la estructura de Factura B si la venta está registrada en AFIP.
**Qué devuelve:** Un `bytearray` con comandos ESC/POS.
**Qué no debe cambiar:** La inicialización (`ESC + \x40`) que resetea la impresora al inicio de cada ticket.
