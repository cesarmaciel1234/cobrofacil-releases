import re
file_path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_setup = '''        self.btn_f5 = create_action_btn("F5", "pagar cuenta", self._f5_pagar_cuenta, style="default")
        lay_ajuste.addWidget(self.btn_f5, 1)

        self.btn_recargo = create_action_btn("F4", "recargo", self.abrir_recargo, style="default")
        lay_imprime.addWidget(self.btn_recargo, 1)
        self.pila_point = QStackedWidget()
        self.pila_point.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_point.setMinimumHeight(78)
        self.btn_f11 = create_action_btn("F11", "Point MP", lambda: self.procesar_pago_mercadopago_point(), style="default")
        self.pila_point.addWidget(self.btn_f11)
        self.pila_point.addWidget(QWidget())
        lay_registra.addWidget(self.pila_point, 1)
        self.pila_extra = QStackedWidget()
        self.pila_extra.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_extra.setMinimumHeight(78)
        self.btn_f12 = create_action_btn("F12", "Verif QR", lambda: self.verificar_transferencia_mp(), style="default")
        self.btn_ultimo = create_action_btn("F12", "último monto", self.corroborar_ultimo_monto, style="default")
        self.pila_extra.addWidget(self.btn_f12)
        self.pila_extra.addWidget(self.btn_ultimo)
        self.pila_extra.addWidget(QWidget())
        lay_ajuste.addWidget(self.pila_extra, 1)'''

new_setup = '''        self.btn_recargo = create_action_btn("F4", "recargo", self.abrir_recargo, style="default")
        lay_imprime.addWidget(self.btn_recargo, 1)
        self.pila_point = QStackedWidget()
        self.pila_point.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_point.setMinimumHeight(78)
        self.btn_f11 = create_action_btn("F11", "Point MP", lambda: self.procesar_pago_mercadopago_point(), style="default")
        self.pila_point.addWidget(self.btn_f11)
        self.pila_point.addWidget(QWidget())
        lay_registra.addWidget(self.pila_point, 1)
        
        self.btn_f5 = create_action_btn("F5", "pagar cuenta", self._f5_pagar_cuenta, style="default")
        self.pila_extra = QStackedWidget()
        self.pila_extra.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_extra.setMinimumHeight(78)
        self.btn_f12 = create_action_btn("F12", "Verif QR", lambda: self.verificar_transferencia_mp(), style="default")
        self.btn_ultimo = create_action_btn("F12", "último monto", self.corroborar_ultimo_monto, style="default")
        self.pila_extra.addWidget(self.btn_f12)
        self.pila_extra.addWidget(self.btn_ultimo)
        self.pila_extra.addWidget(QWidget())
        self.pila_extra.addWidget(self.btn_f5)
        lay_ajuste.addWidget(self.pila_extra, 1)'''

if old_setup in text:
    text = text.replace(old_setup, new_setup)
    print("Replaced setup")
else:
    print("old_setup not found")

old_ajustar = '''        if metodo in ("Mixto", "QR"):
            self.pila_extra.setCurrentIndex(0)
        elif metodo == "Transferencia":
            self.pila_extra.setCurrentIndex(1)
        else:
            self.pila_extra.setCurrentIndex(2)
        
        # F5 solo visible en Fiado y Clientes
        if hasattr(self, "btn_f5"):
            self.btn_f5.setVisible(metodo in ("Fiado", "Clientes"))'''

new_ajustar = '''        if metodo in ("Mixto", "QR"):
            self.pila_extra.setCurrentIndex(0)
        elif metodo == "Transferencia":
            self.pila_extra.setCurrentIndex(1)
        elif metodo in ("Fiado", "Clientes"):
            self.pila_extra.setCurrentIndex(3)
        else:
            self.pila_extra.setCurrentIndex(2)'''

if old_ajustar in text:
    text = text.replace(old_ajustar, new_ajustar)
    print("Replaced ajustar")
else:
    print("old_ajustar not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
