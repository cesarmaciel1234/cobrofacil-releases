import sys

with open('src/carteleria/lanzador_tv/cerebro_lanzador_tv.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """            # Limpiar cache de Chromium para forzar recarga de CSS y JS en cada inicio
            if os.path.exists(self._kiosk_profile):
                shutil.rmtree(self._kiosk_profile, ignore_errors=True)"""

new_code = """            # Limpiar perfiles viejos de Chromium para no llenar el disco
            import glob
            for old_prof in glob.glob(os.path.join(tempfile.gettempdir(), "tpv-carteleria-kiosk-*")):
                if old_prof != self._kiosk_profile:
                    shutil.rmtree(old_prof, ignore_errors=True)"""

content = content.replace(old_code, new_code)

with open('src/carteleria/lanzador_tv/cerebro_lanzador_tv.py', 'w', encoding='utf-8') as f:
    f.write(content)
