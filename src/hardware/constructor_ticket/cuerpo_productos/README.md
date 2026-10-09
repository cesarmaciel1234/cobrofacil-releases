# Cuerpo de Productos

**Qué hace:** Lista los items vendidos dentro del ticket.
**Qué función:** `generar_cuerpo` en `generador.py`
**Cómo funciona:** Itera sobre `items`, formatea limpiando etiquetas como ofertas, e imprime cantidad x precio unitario. Calcula los espacios en blanco para mantener la alineación a la derecha del subtotal (ancho total de 32 caracteres).
**Qué devuelve:** Un `bytearray` con comandos ESC/POS.
**Qué no debe cambiar:** El ancho de 32 columnas para el cálculo de espacios en línea.
