import os

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_str = """        self.estado.setText(f"Hola {nombre}")
        self.detalle.setText(f"Estás a punto de pagar toda la deuda, gracias.\\nSaldo anterior: ${deuda_actual:,.2f}\\nVenta actual: ${self._monto:,.2f}")
        self.icono.hide()
        
        self.txt_monto_abono.setText(f"{monto_sugerido:.2f}")
        self.txt_monto_abono.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()
        
        self.instruccion.setText("[ ENTER ] PARA FINALIZAR VENTA - ¿Con qué querés pagar?")
        self.cont_botones.show()"""

new_str = """        self.estado.setText(f"Hola {nombre}")
        self.detalle.setText(f"Saldo anterior: ${deuda_actual:,.2f}\\nVenta actual: ${self._monto:,.2f}")
        self.icono.hide()
        
        self.txt_monto_abono.setText(f"{monto_sugerido:.2f}")
        self.txt_monto_abono.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()
        
        self.instruccion.hide()
        self.cont_botones.show()"""

if old_str in text:
    text = text.replace(old_str, new_str)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated texts in panel.py")
else:
    print("Could not find text to replace")
