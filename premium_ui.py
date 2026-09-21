import codecs
import re

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# 1. Add DropShadow and signal connection to __init__
pattern_init = r'self\.list_results\.installEventFilter\(self\)'
replacement_init = '''self.list_results.installEventFilter(self)
        
        # Sombra premium para elevarlo a otro nivel
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self.list_results)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.list_results.setGraphicsEffect(shadow)
        
        # Filas alternadas para mejor lectura
        self.list_results.setAlternatingRowColors(True)
        self.list_results.itemSelectionChanged.connect(self._update_search_colors)'''
if re.search(pattern_init, code):
    code = re.sub(pattern_init, replacement_init, code)

# 2. Update QListWidget CSS to support alternating rows smoothly
pattern_css = r'background-color:\s*#F8FAFC;'
replacement_css = '''background-color: #F8FAFC;
                alternate-background-color: #F1F5F9;'''
if re.search(pattern_css, code):
    code = re.sub(pattern_css, replacement_css, code, count=1)

# 3. Add objectNames to labels in _do_busqueda so we can identify them
pattern_labels = r'lbl_n = QLabel\(str\(r\[\'nombre\'\]\)\)\s*lbl_n\.setStyleSheet\(.*?\)\s*lbl_p = QLabel.*?lbl_s = QLabel.*?lay\.addWidget\(lbl_s, 2\)'
replacement_labels = '''lbl_n = QLabel(str(r['nombre']))
                lbl_n.setObjectName("lbl_n")
                lbl_n.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #0F172A;")
                
                lbl_p = QLabel(f"${r['precio']:.2f}")
                lbl_p.setObjectName("lbl_p")
                lbl_p.setStyleSheet("font-size: 18px; font-weight: bold; color: #059669; background: transparent;")
                lbl_p.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                
                lbl_s = QLabel(f"📦 {stk_str}")
                lbl_s.setObjectName("lbl_s")
                lbl_s.setStyleSheet("font-size: 16px; font-weight: bold; color: #64748B; background: transparent;")
                lbl_s.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                lay.addWidget(lbl_n, 5)  # 5 partes para el nombre (Izquierda)
                lay.addWidget(lbl_p, 2)  # 2 partes para el precio (Medio)
                lay.addWidget(lbl_s, 2)  # 2 partes para el stock (Derecha)'''
if re.search(pattern_labels, code, re.DOTALL):
    code = re.sub(pattern_labels, replacement_labels, code, flags=re.DOTALL)

# 4. Insert _update_search_colors method
pattern_method = r'def _layout_list_results_popup'
replacement_method = '''def _update_search_colors(self):
        if not hasattr(self, "list_results"): return
        
        # Cambiamos los colores de los QLabels para que contrasten bien cuando la fila se selecciona (azul)
        for i in range(self.list_results.count()):
            item = self.list_results.item(i)
            w = self.list_results.itemWidget(item)
            if not w: continue
            
            lbl_n = w.findChild(QLabel, "lbl_n")
            lbl_p = w.findChild(QLabel, "lbl_p")
            lbl_s = w.findChild(QLabel, "lbl_s")
            
            if not (lbl_n and lbl_p and lbl_s): continue
            
            if item.isSelected():
                lbl_n.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: white;")
                lbl_p.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: white;")
                lbl_s.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent; color: #E2E8F0;")
            else:
                lbl_n.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #0F172A;")
                lbl_p.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #059669;")
                lbl_s.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent; color: #64748B;")

    def _layout_list_results_popup'''
if re.search(pattern_method, code):
    code = re.sub(pattern_method, replacement_method, code)

# 5. Call it at the end of _do_busqueda
pattern_endbusq = r'self\.list_results\.setCurrentRow\(0\)\s*self\.list_results\.show\(\)'
replacement_endbusq = '''self.list_results.setCurrentRow(0)
            self._update_search_colors()
            self.list_results.show()'''
if re.search(pattern_endbusq, code):
    code = re.sub(pattern_endbusq, replacement_endbusq, code)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Premium UI injected!")
