import codecs

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

from_str = '''                # Si falta dinero y no es mixto, ofrecer pasarse a Mixto
                if self.current_metodo != "Mixto":
                    try:
                        p1_val = float(p1_t) if p1_t else 0.0
                    except ValueError:
                        p1_val = 0.0
                    self.set_metodo("Mixto")
                    faltante = self.total_final - p1_val
                    self.txt_otro.setText(f"{faltante:.2f}")
                    self.txt_otro.setFocus()
                    self.txt_otro.selectAll()
                else:
                    QMessageBox.critical(self, "MONTO INSUFICIENTE", "Falta dinero para cubrir el total.")'''

to_str = '''                # Si falta dinero y no es mixto, lanzar error y obligar al usuario a elegir
                if self.current_metodo != "Mixto":
                    QMessageBox.critical(
                        self, 
                        "MONTO INSUFICIENTE", 
                        "El monto ingresado es menor al total.\\n\\nSi desea realizar un pago con múltiples métodos, haga clic en el botón 'Cambiar' (o presione ESC) y seleccione 'MIXTO'."
                    )
                    self.txt_pago.setFocus()
                    self.txt_pago.selectAll()
                else:
                    QMessageBox.critical(self, "MONTO INSUFICIENTE", "Falta dinero para cubrir el total en el pago mixto.")'''

code = code.replace(from_str, to_str)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Logic fixed!")
