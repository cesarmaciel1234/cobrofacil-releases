# Galería de vitrina

Qué hace: elige, carga, borra y restaura PNG de producto. Ventana grande / pantalla completa (F11).

Qué función: `abrir_galeria`, `DialogoGaleriaVitrina`, `elegir_desde_pc`.

Cómo funciona: lista solo `Catalogos/png_productos/` (sin `__sync__` ni `_anteriores`). Esa carpeta no se rellena con el paquete: queda fija hasta que se genera un PNG nuevo. Miniaturas con `QImageReader` en lotes. Casillero + ✕ para borrar. Crear o cargar pisa el archivo del producto; el anterior va a `_anteriores/` y «Volver al anterior» lo trae.

Qué no debe cambiar: la galería de rubros de inventario (`dialogo_galeria_iconos.py`). Un PNG vivo por producto, no `asado_2.png`.
