import sys
with open('src/carteleria/lanzador_tv/cerebro_lanzador_tv.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'import shutil' not in content:
    content = content.replace('import sys', 'import sys\nimport shutil')

old_code = """    def _lanzar_navegador(self):
        try:
            self._cerrar_navegador()
            url = f"http://{self.host}:{self.port}/\""""

new_code = """    def _lanzar_navegador(self):
        try:
            self._cerrar_navegador()
            
            # Limpiar cache de Chromium para forzar recarga de CSS y JS en cada inicio
            if os.path.exists(self._kiosk_profile):
                shutil.rmtree(self._kiosk_profile, ignore_errors=True)
                
            url = f"http://{self.host}:{self.port}/\""""

content = content.replace(old_code, new_code)

with open('src/carteleria/lanzador_tv/cerebro_lanzador_tv.py', 'w', encoding='utf-8') as f:
    f.write(content)
