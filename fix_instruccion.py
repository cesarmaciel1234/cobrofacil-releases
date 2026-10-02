import os

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_str = """        if hasattr(self, 'txt_monto_abono'):
            self.txt_monto_abono.hide()
        self.instruccion.show()"""

new_str = """        if hasattr(self, 'txt_monto_abono'):
            self.txt_monto_abono.hide()
        self.instruccion.setText(f"[ ENTER ] CONFIRMAR {nombre.upper()}")
        self.instruccion.show()"""

if old_str in text:
    text = text.replace(old_str, new_str)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated panel.py")
else:
    print("Could not find old_str")
