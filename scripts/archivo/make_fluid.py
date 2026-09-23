import codecs

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# 1. Lower search delay
code = code.replace(
    'self.search_timer.start(250)',
    'self.search_timer.start(40)  # Ultra responsivo'
)

# 2. Add an animation to the popup when it shows!
from_str = '''self.list_results.setCurrentRow(0)
            self._update_search_colors()
            self.list_results.show()
            self.list_results.raise_()'''

to_str = '''self.list_results.setCurrentRow(0)
            self._update_search_colors()
            
            # Fluid animation (despliegue suave tipo acordeón)
            if not self.list_results.isVisible():
                from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
                
                # Setup geometry
                self._layout_list_results_popup()
                final_geo = self.list_results.geometry()
                
                # Start small
                start_geo = QRect(final_geo.x(), final_geo.y() + final_geo.height(), final_geo.width(), 0)
                self.list_results.setGeometry(start_geo)
                self.list_results.show()
                self.list_results.raise_()
                
                # Animate
                self.anim = QPropertyAnimation(self.list_results, b"geometry")
                self.anim.setDuration(150)
                self.anim.setStartValue(start_geo)
                self.anim.setEndValue(final_geo)
                self.anim.setEasingCurve(QEasingCurve.Type.OutQuart)
                self.anim.start()
            else:
                self.list_results.show()
                self.list_results.raise_()'''

code = code.replace(from_str, to_str)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Fluid animations added!")
