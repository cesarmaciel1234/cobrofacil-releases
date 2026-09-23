import codecs

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

from_str = '''            if k in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
                # Desviar flechas a la navegación de métodos de pago
                methods = list(self.btns.keys())
                try:
                    curr_idx = methods.index(self.current_metodo)
                except ValueError:
                    curr_idx = 0
                
                if k == Qt.Key_Left: next_idx = (curr_idx - 1) % len(methods)
                elif k == Qt.Key_Right: next_idx = (curr_idx + 1) % len(methods)
                elif k == Qt.Key_Up: next_idx = (curr_idx - 5) % len(methods)
                elif k == Qt.Key_Down: next_idx = (curr_idx + 5) % len(methods)
                
                self.set_metodo(methods[next_idx])
                return True # Consumir evento
            elif event.type() == QEvent.FocusOut:'''

to_str = '''            # LAS FLECHAS YA NO CAMBIAN EL MÉTODO (Lógica nueva)
            # Solo permiten moverse dentro del QLineEdit
            elif event.type() == QEvent.FocusOut:'''

code = code.replace(from_str, to_str)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Arrows fixed!")
