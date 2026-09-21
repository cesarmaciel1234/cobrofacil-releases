import codecs
import re

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

pattern = r'self\.list_results\.setCurrentRow\(0\)\s*self\._update_search_colors\(\)\s*self\.list_results\.show\(\)\s*self\.list_results\.raise_\(\)'

replacement = '''self.list_results.setCurrentRow(0)
            self._update_search_colors()
            
            # Fluid animation (despliegue suave tipo acordeón ascendente ya que está anclado abajo)
            if not self.list_results.isVisible():
                from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
                
                # Configurar geometría final
                self._layout_list_results_popup()
                final_geo = self.list_results.geometry()
                
                # Iniciar con altura 0, alineado al fondo (pegado a la caja de texto)
                start_geo = QRect(final_geo.x(), final_geo.y() + final_geo.height(), final_geo.width(), 0)
                self.list_results.setGeometry(start_geo)
                self.list_results.show()
                self.list_results.raise_()
                
                # Animar altura y posición Y simultáneamente para efecto de "crecimiento hacia arriba"
                self.anim = QPropertyAnimation(self.list_results, b"geometry")
                self.anim.setDuration(200)  # 200ms de pura suavidad
                self.anim.setStartValue(start_geo)
                self.anim.setEndValue(final_geo)
                self.anim.setEasingCurve(QEasingCurve.Type.OutQuart) # Aceleración suave
                self.anim.start()
            else:
                self.list_results.show()
                self.list_results.raise_()'''

if re.search(pattern, code):
    code = re.sub(pattern, replacement, code)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Animation applied!")
else:
    print("Pattern not found!")
