import sys
file_path = 'src/contabilidad/jefe_contabilidad.py'
with open(file_path, 'a', encoding='utf-8') as f:
    f.write('''
    def _init_motor_sync(self):
        try:
            from src.contabilidad.integracion_maestra.motor_sync_conta import MotorSyncConta
            self.motor_sync = MotorSyncConta(self._db, self)
            self.motor_sync.sync_finished.connect(self._on_sync_finished)
            self.motor_sync.start()
        except Exception as e:
            print(f"Error iniciando MotorSyncConta: {e}")

    def _on_sync_finished(self, pushed, pulled):
        print(f"[Contabilidad] Sincronización automática: {pushed} subidos, {pulled} bajados.")
        self._reload_current_tab()
''')
