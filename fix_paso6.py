import os

file_path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_code = """        if hasattr(self, "panel_fiado") and self.panel_fiado.hoja_cuenta.isVisible():
            self.panel_fiado.hoja_cuenta.fijar_monto(self.total_final)"""
new_code = """        if hasattr(self, "panel_fiado"):
            if self.panel_fiado.hoja_cuenta.isVisible():
                self.panel_fiado.hoja_cuenta.fijar_monto(self.total_final)
            if hasattr(self.panel_fiado, "actualizar_monto"):
                self.panel_fiado.actualizar_monto(self.total_final)"""

text = text.replace(old_code, new_code)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
