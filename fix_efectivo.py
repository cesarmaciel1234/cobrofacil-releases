import os

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_efectivo_logic = """        if metodo == "Efectivo":
            if not self._pin():
                return
            self._finalizar_cobranza_con_motor(monto, metodo, None)
            return"""

new_efectivo_logic = """        # Pasamos al lienzo efectivo en vez de saltarlo"""

text = text.replace(old_efectivo_logic, new_efectivo_logic)

old_arrancar = """        if metodo == "QR":"""
new_arrancar = """        if metodo == "Efectivo":
            self.cont_lienzos.setCurrentWidget(self.lienzo_efectivo)
            self.lienzo_efectivo.arrancar(monto)
        elif metodo == "QR":"""
text = text.replace(old_arrancar, new_arrancar)

# Y en _finalizar_cobranza_con_motor pedir PIN si es Efectivo:
old_fin = """        res = ResultadoMedio(True, metodo, (metodo == "Efectivo"), detalle)"""
new_fin = """        if metodo == "Efectivo":
            if not self._pin():
                self._volver_de_lienzo()
                return
        res = ResultadoMedio(True, metodo, (metodo == "Efectivo"), detalle)"""
text = text.replace(old_fin, new_fin)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
