import os

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_func = '''    def actualizar_monto(self, nuevo_monto_venta):
        self._monto = nuevo_monto_venta
        if getattr(self, "_modo", "") in ("cobranza", "cobrando_lienzo"):
            deuda = getattr(self, "_deuda_actual", 0.0)
            monto_sugerido = nuevo_monto_venta + deuda
            self.detalle.setText(f"Saldo anterior: ${deuda:,.2f}\\nVenta actual: ${self._monto:,.2f}")
            if getattr(self, "_modo", "") == "cobranza":
                self.txt_monto_abono.setText(f"{monto_sugerido:.2f}".replace('.', ','))'''

new_func = '''    def actualizar_monto(self, nuevo_monto_venta):
        self._monto = nuevo_monto_venta
        if getattr(self, "_modo", "") in ("cobranza", "cobrando_lienzo"):
            if getattr(self, "_modo", "") == "cobrando_lienzo":
                # Si cambian el total (ej F3) mientras esta el QR/Tarjeta activo, abortamos el lienzo
                # forzando a que vuelvan a generarlo con el monto correcto.
                self._volver_de_lienzo()
            deuda = getattr(self, "_deuda_actual", 0.0)
            monto_sugerido = nuevo_monto_venta + deuda
            self.detalle.setText(f"Saldo anterior: ${deuda:,.2f}\\nVenta actual: ${self._monto:,.2f}")
            self.txt_monto_abono.setText(f"{monto_sugerido:.2f}".replace('.', ','))'''

if old_func in text:
    text = text.replace(old_func, new_func)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated successfully!')
else:
    print('Could not find old_func')
