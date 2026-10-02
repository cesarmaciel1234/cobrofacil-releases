with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'r', encoding='utf8') as f:
    text = f.read()
lines = text.split('\n')
out = []
for l in lines:
    if 'self.txt_monto_abono.installEventFilter(self)' in l:
        pass # remove the bad ones
    elif l.strip() == 'self.txt_monto_abono.hide()':
        out.append(l)
        out.append('        self.txt_monto_abono.installEventFilter(self)')
    elif l.startswith('    def resizeEvent'):
        out.append('    def eventFilter(self, obj, event):')
        out.append('        if obj == self.txt_monto_abono and event.type() == event.Type.KeyPress:')
        out.append('            if event.key() == Qt.Key.Key_Escape:')
        out.append('                self._al_cliente_encontrado(self._cliente_id)')
        out.append('                return True')
        out.append('            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):')
        out.append('                self.procesar_enter()')
        out.append('                return True')
        out.append('        return super().eventFilter(obj, event)')
        out.append('')
        out.append(l)
    else:
        out.append(l)

with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'w', encoding='utf8') as f:
    f.write('\n'.join(out))