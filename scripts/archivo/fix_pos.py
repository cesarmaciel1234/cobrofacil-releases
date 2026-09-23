import codecs
import re

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

pattern = r'def _layout_list_results_popup\(self, metrics=None\):.*?self\.list_results\.setGeometry\(x, max\(0, y\), w, h\)'

replacement = '''def _layout_list_results_popup(self, metrics=None):
        if not hasattr(self, "list_results") or not hasattr(self, "txt_scan"):
            return
        
        # Ancho 75% de la pantalla para buena lectura, Alto 65% de la tabla
        w = int(self.width() * 0.75)
        h = int(self.dashboard_frame.height() * 0.65) if hasattr(self, "dashboard_frame") else 350
        
        if w < 600: w = 600
        if h < 300: h = 300
        
        from PyQt6.QtCore import QPoint
        # Mapeamos las coordenadas de la caja de texto (txt_scan) hacia la ventana (self)
        pos = self.txt_scan.mapTo(self, QPoint(0, 0))
        
        # Alineamos el borde izquierdo del popup con el borde izquierdo del buscador
        x = pos.x()
        
        # El borde inferior del popup debe estar justo encima del buscador (pos.y() - altura - 5px margen)
        y = pos.y() - h - 5
        
        self.list_results.setGeometry(x, max(0, y), w, h)'''

if re.search(pattern, code, re.DOTALL):
    code = re.sub(pattern, replacement, code, flags=re.DOTALL)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Fixed popup position!")
else:
    print("Pattern not found!")
