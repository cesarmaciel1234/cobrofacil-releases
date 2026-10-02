import os

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# We need to replace the following lines in `_al_cliente_encontrado`:
#         self.icono.show()
#         self.estado.setText(f"FIADO APROBADO\n{nombre}")
#         self.detalle.setText(
#             f"Límite Disponible: ${disp:,.2f}\nCompra Actual: ${self._monto:,.2f}"
#         )

import re

# Use regex to find and replace
pattern = r"self\.icono\.show\(\)\s*self\.estado\.setText\(f\"FIADO APROBADO\\n\{nombre\}\"\)\s*self\.detalle\.setText\(\s*f\"L[^\n]+\\n[^\n]+\"\s*\)"

replacement = """self.icono.hide()
        self.estado.setText("FIADO APROBADO")
        self.detalle.setText(f"{nombre}")
        if hasattr(self, 'txt_monto_abono'):
            self.txt_monto_abono.hide()"""

text = re.sub(pattern, replacement, text)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

