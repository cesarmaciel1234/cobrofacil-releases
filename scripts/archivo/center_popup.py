import codecs
import re

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# Fix margins and height
pattern_margins = r'lay\.setContentsMargins\(10,\s*2,\s*10,\s*2\)'
replacement_margins = '''lay.setContentsMargins(15, 12, 15, 12)
                w.setMinimumHeight(60)'''
if re.search(pattern_margins, code):
    code = re.sub(pattern_margins, replacement_margins, code)

# Center popup
pattern_layout = r'def _layout_list_results_popup\(self,\s*metrics=None\):.*?self\.list_results\.setGeometry\(.*?\)'
replacement_layout = '''def _layout_list_results_popup(self, metrics=None):
        if not hasattr(self, "list_results") or not hasattr(self, "dashboard_frame"):
            return
        
        # Hacemos que sea el centro de atención (enfoque total) sobre la tabla principal
        db = self.dashboard_frame
        w = int(db.width() * 0.8)
        h = int(db.height() * 0.7)
        
        # Validar tamanos minimos
        if w < 500: w = 500
        if h < 300: h = 300
        
        x = db.x() + int((db.width() - w) / 2)
        y = db.y() + int((db.height() - h) / 2)
        
        self.list_results.setGeometry(x, max(0, y), w, h)'''

if re.search(pattern_layout, code, re.DOTALL):
    code = re.sub(pattern_layout, replacement_layout, code, flags=re.DOTALL)

# Let's also add some drop shadow and thicker border to QListWidget for better visual separation
pattern_style = r'QListWidget \{\s*border:\s*2px solid #3B82F6;\s*border-radius:\s*8px;'
replacement_style = '''QListWidget {
                border: 4px solid #3B82F6;
                border-radius: 12px;'''
if re.search(pattern_style, code):
    code = re.sub(pattern_style, replacement_style, code)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Fixed layout, margins, and center popup!")
