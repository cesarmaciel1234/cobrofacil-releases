import os

file_path = 'src/clientes_fiado/interfaz/cobro/hoja.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_event_filter = '''    def eventFilter(self, obj, event):
        if obj is self.caja and event.type() == QEvent.Type.KeyPress and getattr(self, "lista", None) and self.lista.isVisible():
            tecla = event.key()
            if tecla == Qt.Key.Key_Down and self._filas:
                self.lista.setFocus()
                return True
        if obj is self.caja and event.type() == QEvent.Type.KeyPress and getattr(self, "_pidiendo_pin", False):'''

new_event_filter = '''    def eventFilter(self, obj, event):
        if obj is self.caja and event.type() == QEvent.Type.KeyPress and getattr(self, "_pidiendo_pin", False):'''

if old_event_filter in text:
    text = text.replace(old_event_filter, new_event_filter)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Fixed eventFilter.')
else:
    print('old_event_filter not found.')
