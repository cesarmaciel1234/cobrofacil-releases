import sys

file_path = "src/clientes_fiado/interfaz/cobro/hoja.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

old_pintar_paso = '''    def _pintar_paso(self):
        self._silencio = True
        self.aviso.setTextFormat(Qt.TextFormat.PlainText)
        self.aviso.setStyleSheet("color: #EF4444; font-size: 18px; font-weight: 800;")
        self.aviso.clear()
        self.caja.clear()
        self._silencio = False
        self._cerrar_lista()
        self.subtitulo.hide()
        if self._modo == "Fiado":
            self.caja.setValidator(self._val_dni)
            self.caja.setPlaceholderText("DNI")
        else:
            self.caja.setValidator(self._val_nombre)
            self.caja.setPlaceholderText("Nombre")
        if self._paso == 2 and self._cliente:
            cartel = cerebro.cartel(self._cliente)
            self.texto.setText(str(cartel.get("saludo") or "Sin datos"))
            self.texto.setStyleSheet("color: #0F172A; font-size: 32px; font-weight: 900;")
            self.subtitulo.setText("¿Desea enviar la compra a la cuenta del cliente?")
            self.subtitulo.show()
            self._pintar_numeros(cartel.get("saldo"), cartel.get("disponible"))
            
            self.caja.hide()
            self.caja.clearFocus()
            self.btn_f4.show()
            self.btn_enter.show()
            self.setFocus()
        else:
            self.caja.show()
            self.btn_f4.hide()
            if hasattr(self, 'btn_enter'):
                self.btn_enter.hide()
            self.texto.setText(self._frase())
            self.texto.setStyleSheet("color: #1E3A8A; font-size: 28px; font-weight: 800;")
            self.saldo.clear()
            self.disponible.clear()
            self.caja.setFocus()'''

new_pintar_paso = '''    def _pintar_paso(self):
        self._silencio = True
        self.aviso.setTextFormat(Qt.TextFormat.PlainText)
        self.aviso.setStyleSheet("color: #EF4444; font-size: 18px; font-weight: 800;")
        self.aviso.clear()
        self.caja.clear()
        self._silencio = False
        self._cerrar_lista()
        self.subtitulo.hide()
        if self._modo == "Fiado":
            self.caja.setValidator(self._val_dni)
            self.caja.setPlaceholderText("DNI")
        else:
            self.caja.setValidator(self._val_nombre)
            self.caja.setPlaceholderText("Nombre")
        if self._paso == 2 and self._cliente:
            self.setStyleSheet(
                "QFrame#HojaCuenta {"
                " background: #ECFDF5; border: 2px solid #34D399; border-radius: 22px;"
                "}"
                "QLabel { background: transparent; border: none; }"
            )
            cartel = cerebro.cartel(self._cliente)
            self.texto.setText("✔\\n\\nFIADO APROBADO")
            self.texto.setStyleSheet("color: #047857; font-size: 26px; font-weight: 900;")
            
            saludo = str(cartel.get("saludo") or "")
            nombre_cliente = saludo.replace("Hola, ", "")
            self.subtitulo.setText(nombre_cliente)
            self.subtitulo.setStyleSheet("color: #047857; font-size: 22px; font-weight: 800;")
            self.subtitulo.show()
            
            disp = cartel.get("disponible") or 0.0
            self.saldo.setText(f"Límite Disponible: ${float(disp):,.2f}")
            self.saldo.setStyleSheet("color: #047857; font-size: 16px; font-weight: 700;")
            
            self.disponible.setText(f"Compra Actual: ${float(self._monto):,.2f}")
            self.disponible.setStyleSheet("color: #047857; font-size: 16px; font-weight: 700;")
            
            self.caja.hide()
            self.caja.clearFocus()
            self.btn_f4.hide()
            self.btn_enter.setText("[ ENTER ] CONFIRMAR FIADO")
            self.btn_enter.setStyleSheet("color: #FFFFFF; background: #10B981; font-size: 18px; font-weight: 900; border-radius: 8px; padding: 14px; margin-top: 10px;")
            self.btn_enter.show()
            self.setFocus()
        else:
            self.setStyleSheet(
                "QFrame#HojaCuenta {"
                " background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 22px;"
                "}"
                "QLabel { background: transparent; border: none; }"
            )
            self.caja.show()
            self.btn_f4.hide()
            if hasattr(self, 'btn_enter'):
                self.btn_enter.setText("[ ENTER ] FIAR COMPRA ACTUAL")
                self.btn_enter.setStyleSheet("color: #FFFFFF; background: #10B981; font-size: 16px; font-weight: 800; border-radius: 8px; padding: 12px; margin-top: 6px;")
                self.btn_enter.hide()
            self.texto.setText(self._frase())
            self.texto.setStyleSheet("color: #1E3A8A; font-size: 28px; font-weight: 800;")
            self.saldo.setStyleSheet("color: #0F172A; font-size: 28px; font-weight: 900;")
            self.disponible.setStyleSheet("color: #047857; font-size: 28px; font-weight: 900;")
            self.saldo.clear()
            self.disponible.clear()
            self.caja.setFocus()'''

# The encoding might have funny characters so we should be careful to handle the "¿" properly in the original code.
# Notice the original code has self.subtitulo.setText("¿Desea enviar la compra a la cuenta del cliente?") but powershell logs might show "".
# The actual file has "¿". Let's replace the block safely using regex or just find the start/end bounds.

import re

# Safely extract the `def _pintar_paso(self):` block till `def _pintar_numeros`
match = re.search(r'    def _pintar_paso\(self\):.*?    def _pintar_numeros\(self, saldo, disponible\):', code, re.DOTALL)
if match:
    old_block = match.group(0).replace('    def _pintar_numeros(self, saldo, disponible):', '')
    code = code.replace(old_block, new_pintar_paso + "\\n\\n")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    print("Patched successfully!")
else:
    print("Could not find block")
