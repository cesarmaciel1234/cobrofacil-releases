with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'r', encoding='utf8') as f:
    text = f.read()

# I will add an event filter or key press to QLineEdit so ESC returns to 'confirmando'
text = text.replace(
    'self.txt_monto_abono.hide()',
    'self.txt_monto_abono.hide()\n        self.txt_monto_abono.installEventFilter(self)'
)

event_filter_code = '''
    def eventFilter(self, obj, event):
        if obj == self.txt_monto_abono and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self._al_cliente_encontrado(self._cliente_id) # Volver al modo confirmando
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.procesar_enter()
                return True
        return super().eventFilter(obj, event)
'''

text = text.replace(
    'def resizeEvent(self, event):',
    event_filter_code.lstrip() + '\n    def resizeEvent(self, event):'
)

with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'w', encoding='utf8') as f:
    f.write(text)