import re
file_path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_abono = '''    def _abono_cuenta_registrado(self, resultado):
        from src.utils.dinero import redondear_dinero

        if self.deuda_adicional_saldo_anterior is None:
            self.deuda_adicional_saldo_anterior = float(resultado.deuda_anterior or 0)
        self.deuda_adicional_cobrada = redondear_dinero(
            self.deuda_adicional_cobrada + float(resultado.monto or 0)
        )
        self._avisar(
            f"Abono a cuenta registrado: ${float(resultado.monto):,.2f}. "
            "La venta sigue a Fiado."
        )'''

new_abono = '''    def _abono_cuenta_registrado(self, resultado):
        from src.utils.dinero import redondear_dinero

        if self.deuda_adicional_saldo_anterior is None:
            self.deuda_adicional_saldo_anterior = float(resultado.deuda_anterior or 0)
        self.deuda_adicional_cobrada = redondear_dinero(
            self.deuda_adicional_cobrada + float(resultado.monto or 0)
        )
        self._avisar(f"Abono a cuenta registrado: ${float(resultado.monto):,.2f}.")
        # El abono ya entró a la cuenta, ahora finalizamos la venta actual enviándola a Fiado
        # para que se descuente del saldo a favor o se sume a la deuda que quede.
        self._cuenta_lista(resultado.cliente_id)'''

if old_abono in text:
    text = text.replace(old_abono, new_abono)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed abono auto-finalize")
else:
    print("old_abono not found")
