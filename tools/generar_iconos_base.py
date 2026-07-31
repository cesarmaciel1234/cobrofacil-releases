import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QFont, QColor
from PyQt6.QtCore import Qt, QRectF

def generar_iconos_perfectos():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
        
    target_dir = os.path.join(os.getcwd(), "Catalogos", "iconos_rubros")
    os.makedirs(target_dir, exist_ok=True)
    
    icons = [
        ('carne.png', '🥩'),
        ('pollo.png', '🍗'),
        ('cerdo.png', '🥓'),
        ('fiambreria.png', '🧀'),
        ('panaderia.png', '🍞'),
        ('verduleria.png', '🥦'),
        ('bebidas.png', '🥤'),
        ('limpieza.png', '🧹'),
        ('almacen.png', '📦'),
        ('pescado.png', '🐟'),
        ('oferta.png', '🔥'),
        ('varios.png', '⭐')
    ]
    
    for filename, emoji in icons:
        # Canvas 160x160 transparente
        img = QImage(160, 160, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Tamaño 80pt para evitar que la métrica del tipo de letra recorte la parte superior/inferior
        font = QFont('Segoe UI Emoji', 80)
        painter.setFont(font)
        painter.setPen(QColor('#FFFFFF'))
        painter.drawText(QRectF(0, 0, 160, 160), Qt.AlignmentFlag.AlignCenter, emoji)
        
        painter.end()
        out_path = os.path.join(target_dir, filename)
        img.save(out_path)
        print(f"Generado ícono completo sin recorte: {out_path}")

if __name__ == "__main__":
    generar_iconos_perfectos()
