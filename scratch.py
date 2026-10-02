import sys

path = 'src/clientes_fiado/interfaz/cobro/hoja.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_block = r'''        self\.aviso\.setStyleSheet\("color: #047857; font-size: 18px; font-weight: 800;"\)
        self\.aviso\.setText\(
            f"Abono registrado: \$\{resultado\.monto:,\.2f\}\. "
            "Presione Enter para continuar la venta a Fiado\."
            if not resultado\.aviso
            else resultado\.aviso
        \)
        self\.abono_registrado\.emit\(resultado\)
        self\.setFocus\(\)'''

new_block = '''        self.abono_registrado.emit(resultado)
        # FLUJO FLUIDO: Emite ok al motor de cobro inmediatamente como una venta normal
        self.listo.emit(int(self._cliente.get("id")), 0.0)'''

if re.search(old_block, text):
    new_text = re.sub(old_block, new_block, text)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Updated _abrir_dialogo_cobranza in hoja.py (Fluido)")
else:
    print("Could not find exact block in hoja.py")