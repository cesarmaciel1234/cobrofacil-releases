import re
file_path = 'src/contabilidad/jefe_contabilidad.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'def __init__\(self, parent=None, db=None\):(.*?)self\._setup_ui\(\)'
def repl(match):
    return '''def __init__(self, parent=None, db=None):''' + match.group(1) + '''self._setup_ui()
        self._init_motor_sync()

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
        self._reload_current_tab()'''

text = re.sub(pattern, repl, text, flags=re.DOTALL)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
