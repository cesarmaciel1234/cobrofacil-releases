
file_path = 'src/contabilidad/integracion_maestra/motor_sync_conta.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

injection = '''
                # Sincronizar ventas automaticamente (TPV -> Contabilidad)
                try:
                    from src.contabilidad.integracion_maestra.sincronizador import SincronizadorMaestra
                    sinc = SincronizadorMaestra(self.db_conta)
                    if sinc.traer_ventas_del_dia():
                        # Notificar refresco de UI si trajo algo nuevo (el sincr devuelve True si no hay error)
                        # Idealmente, checkeamos si hubo cambios, pero traer_ventas_del_dia hace insert... 
                        # el loop normal despues hace emit de sync_finished
                        pass
                except Exception as e:
                    print(f'[MotorConta] Error importando ventas auto: {e}')

                self._asegurar_esquemas()
'''
text = text.replace('self._asegurar_esquemas()', injection)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Injected')

