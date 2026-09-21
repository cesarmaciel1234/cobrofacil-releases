import codecs
import re

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# Let's find the corrupted block starting from 'try:' down to 'if exito:'
pattern = r'try:\s*from src\.cajero\.cajero_activo import CajeroActivo.*?if exito:'

repl = '''try:
            from src.cajero.cajero_activo import CajeroActivo
            cajero_secundario = CajeroActivo.nombre if CajeroActivo.numero == 2 else ''
            cajero_actual = dict(config.current_user).get('username', 'cajero') if config.current_user else 'cajero'
            cliente_id = getattr(self, "_fiado_cliente_id", None) or self.cmb_cliente.currentData()
            
            from src.cajero.paso6_cobro.motor_pagos.motor_principal import MotorPrincipalCobros
            
            datos_orden = {
                "total_final": self.total_final,
                "p1": p1,
                "p2": p2,
                "items_carrito": self.items_carrito,
                "cajero": cajero_actual,
                "cajero_sec": cajero_secundario,
                "descuento": getattr(self, 'descuento_monto', 0.0),
                "recargo": getattr(self, 'recargo_monto', 0.0),
                "oferta": getattr(self, 'descuentaso_oferta', 0.0),
                "nombre_pendiente": getattr(self, 'nombre_pendiente', None),
                "cliente_id": cliente_id,
                "imprimir": imprimir,
                "force_fiscal": force_fiscal
            }
            
            exito, mensaje = MotorPrincipalCobros.iniciar_transaccion(
                metodo=self.current_metodo,
                datos_ui=datos_orden
            )
            
            if exito:'''

code = re.sub(pattern, repl, code, flags=re.DOTALL)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Syntax fixed!")
