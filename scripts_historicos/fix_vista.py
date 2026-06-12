import codecs

# Fix vista_historial
with codecs.open('src/jefe/reportes/vista_historial.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('class DialogoHistorialDia(QDialog):', 'class VistaHistorial(QWidget):')
text = text.replace('def __init__(self, parent=None, is_embedded=False):', 'def __init__(self, parent=None):')
text = text.replace('        self.is_embedded = is_embedded', '')
text = text.replace('        if not is_embedded:', '        if False:')
text = text.replace('        else:', '        if True:')
text = text.replace('        if not is_embedded:\\n            self.apply_glow()', '')
text = text.replace("if self.is_embedded and hasattr(self, 'btn_close'):", "if hasattr(self, 'btn_close'):")

# We should also hide the close button explicitly
text = text.replace("self.btn_close.clicked.connect(self.accept)", "self.btn_close.hide()")
text = text.replace("self.btn_close.clicked.connect(self.close)", "self.btn_close.hide()")

with codecs.open('src/jefe/reportes/vista_historial.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed vista_historial.py")
