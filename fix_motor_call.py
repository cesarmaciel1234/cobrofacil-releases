import codecs
import re

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

from_str = '''            from src.cajero.paso6_cobro.componentes_paso6_cobro.logica.cobro_controller import CobroController
            
            exito, mensaje = CobroController.completar_transaccion(
                total_final=self.total_final,
                metodo=self.current_metodo,
                p1=p1,
                p2=p2,
                items_carrito=self.items_carrito,
                cajero=cajero_actual,
                cajero_sec=cajero_secundario,
                descuento=getattr(self, 'descuento_monto', 0.0),
                recargo=getattr(self, 'recargo_monto', 0.0),
                oferta=getattr(self, 'descuentaso_oferta', 0.0),
                nombre_pendiente=getattr(self, 'nombre_pendiente', None),
                cliente_id=cliente_id,
                imprimir=imprimir,
                force_fiscal=force_fiscal
            )'''

to_str = '''            from src.cajero.paso6_cobro.motor_pagos.motor_principal import MotorPrincipalCobros
            
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
            )'''

if from_str in code:
    code = code.replace(from_str, to_str)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Motor Principal integrado en paso6_cobro.py!")
else:
    print("Could not find the target string in paso6_cobro.py")
